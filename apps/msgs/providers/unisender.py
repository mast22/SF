from .base_provider import BaseProvider
from ..const import MessageSendResult, MessageStatus, MessageType
from ..utils import make_request
from ..exceptions import ProviderKeyError


class UnisenderProvider(BaseProvider):
    PROVIDE = {  # Действия, предоставляемые провайдером
        MessageType.DIALING: 'send_dialing',  # Отправка проверочного кода
        MessageType.SMS: 'send_sms',  # Отправка СМС-сообщения на один или несколько номеров
        MessageType.EMAIL: 'send_email',  # Отправка email
    }
    AUTH_CODE_METHODS = { 'SMS', }
    NOTIFICATION_METHODS = { 'EMAIL', }

    DEFAULT_SETTINGS = {
        'send_sms_url': 'https://api.unisender.com/ru/api/sendSms',
        'send_email_url': 'https://api.unisender.com/ru/api/sendEmail',
        'send_transactional_email_url': 'https://one.unisender.com/ru/transactional/api/v1/email/send.json',
        'get_sms_status_url': 'https://api.unisender.com/ru/api/checkSms',
        'get_email_status_url': 'https://www.unisender.com/ru/support/api/messages/check-email/',
        'get_balance_url': 'https://one.unisender.com/ru/transactional/api/v1/balance.json',
    # FIXME: Только для транзакционных email-ов!!!
        'use_transactional': False,  # Отправлять через спец. сервис транзакционных email
        # Обязательные параметры:
        'api_key': None,
        'login': None,
        'sms_from': None,  # Имя отправителя SMS
        'email_from': None,
        'email_from_name': None,
    }

    # def __init__(self, settings, **options):
    #     super(UnisenderProvider, self).__init__(settings, **options)

    def send_sms(self, to=None, receivers=None, text=None, options=None):
        options = options if options else { }
        url = self.settings['send_sms_url']
        resp = make_request(url, method='POST', params={
            'format': 'json',
            'api_key': options.get('api_key', self.settings['api_key']),
            'sender': options.get('sms_from', self.settings['sms_from']),
            'phone': to,
            'text': text,
        }, req_type='JSON', resp_type='JSON')
        result = resp.get('result', None)
        if result:
            self.msg_id = result.get('sms_id')
            return MessageSendResult(
                True, self.msg_id, None, None
            )
        else:
            self.error_code = resp.get('code', None)
            self.error_descr = resp.get('message', None)
            return MessageSendResult(
                False, None, None, self.error_code, self.error_descr
            )

    def get_sms_status(self, msg_uuid: str = None, options=None):
        options = options if options else { }
        self.error_code = self.error_descr = None
        url = self.settings['get_sms_status_url']
        sms_id = msg_uuid if msg_uuid else self.msg_id
        if not sms_id:
            raise ProviderKeyError('There is no msg_uuid available to check')
        resp = make_request(url, method='POST', params={
            'format': 'json',
            'api_key': options.get('api_key', self.settings['api_key']),
            'sms_id': sms_id,
        }, req_type='JSON', resp_type='JSON')
        result = resp.get('result', None)
        delivered = False
        if result:
            status_code = result.get('status')
            if status_code == 'ok_delivered':
                delivered = True
            else:
                self.error_code = status_code if status_code != 'ok_sent' else status_code
        else:
            self.error_code = resp.get('code', None)
            self.error_descr = resp.get('message', None)
        return MessageStatus(
            delivered, self.error_code, self.error_descr, False, False
        )

    def send_email(self, to=None, receivers=None, text='', subject='', attachments=None, options=None):
        options = options if options else { }
        transactional = options.get('use_transactional', self.settings['use_transactional'])
        if not receivers:
            receivers = (to,)
        is_html = options.get('is_html', False)
        body = {
            'html': text if is_html else None,
            'txt': text if not is_html else None
        }
        if transactional:
            return self._send_transactional_email(receivers, subject, body, attachments, options)
        else:
            return self._send_normal_email(receivers, subject, body, attachments, options)

    def _send_transactional_email(self, receivers, subject, body, attachments, options):
        url = self.settings['send_transactional_email_url']
        data = {
            'api_key': options.get('apiKey', self.settings['api_key']),
            'username': options.get('login', self.settings['login']),
            'message': {
                'template_engine': 'simple',
                'body': {
                    'html': body.get('html', None),
                    'plaintext': body.get('txt', None),
                },
                'subject': subject if subject is not None else self.settings['email_subject'],
                'from_email': options.get('from_email', self.settings['email_from']),
                'from_name': options.get('from_name', self.settings['email_from_name']),
                'track_links': 0,
                'track_read': 1,
                'recipients': [{ 'email': to, } for to in receivers],
            }
        }
        if attachments:
            data['inline_attachments'] = []
            for att in attachments:
                data['inline_attachments'].append({
                    'type': att['type'],
                    'name': att['name'],
                    'content': att['data']
                })

        resp = make_request(url, method='POST', data=data, req_type='JSON', resp_type='JSON')
        self.msg_id = resp.get('job_id', None)
        status = resp.get('status', None)
        if status == 'error':
            self.error_code = resp.get('code', None)
            self.error_descr = resp.get('message', None)
        email_sended = not (self.msg_id is None and self.error_code)

        return MessageSendResult(
            email_sended,
            self.msg_id,
            None,
            self.error_code,
            self.error_descr
        )

    def _send_normal_email(self, receivers, subject, body, attachments, options):
        url = self.settings['send_email_url']
        params = {
            'format': 'json',
            'api_key': options.get('api_key', self.settings['api_key']),
            'email': receivers,
            'sender_name': options.get('from_name', self.settings['from_name']),
            'sender_email': options.get('from_email', self.settings['from_email']),
            'subject': subject,
            'body': body.get('html', body.get('txt', None)),
            'list_id': None,
        # Код списка, от которого будет предложено отписаться адресату в случае, если он перейдёт по ссылке отписки. См: getLists. (https://www.unisender.com/ru/support/api/contacts/getlists/)
        }
        if attachments:
            for att in attachments:
                params['attachments[{0}]'.format(att['name'])] = att['content']

        resp = make_request(url, method='POST', params=params)
        resp = resp.get('result', [{ }])[0]
        self.msg_id = resp.get('id', None)
        errors = resp.get('errors', [])
        self.error_code = errors[0].get('code', None)
        self.error_descr = errors[0].get('descr', None)
        email_sended = not (self.msg_id is None and self.error_code)

        return MessageSendResult(
            email_sended,
            self.msg_id,
            None,
            self.error_code,
            self.error_descr
        )

    def send_mass_email(self, receivers, subject, body, attachments, options):
        """https://api.unisender.com/ru/api/createEmailMessage?format=json&api_key=KEY&sender_name=FROMNAME&sender_email=
        FROMMAIL&
        subject=SUBJECT&
        body=HTMLBODY &
        list_id=X&tag=TAG&
        attachements=FILESARRAY&
        lang=LANG&
        wrap_type=STRING&
        text_body=TEXTBODY&
        generate_text=GENERATETEXT &
        categories=CATEGORIES"""
        url = self.settings['send_email_url']
        params = {
            'format': 'json',
            'api_key': options.get('api_key', self.settings['api_key']),
            'sender_name': options.get('from_name', self.settings['from_name']),
            'sender_email': options.get('from_email', self.settings['from_email']),
            'subject': subject,
            'body': body.get('html', body.get('txt', None)),
            'list_id': None,
        # Код списка, от которого будет предложено отписаться адресату в случае, если он перейдёт по ссылке отписки. См: getLists. (https://www.unisender.com/ru/support/api/contacts/getlists/)
        }
        if attachments:
            for att in attachments:
                params['attachments[{0}]'.format(att['name'])] = att['content']

        resp = make_request(url, method='POST', params=params)
        resp = resp.get('result', [{ }])[0]
        self.msg_id = resp.get('id', None)
        errors = resp.get('errors', [])
        self.error_code = errors[0].get('code', None)
        self.error_descr = errors[0].get('descr', None)
        email_sended = not (self.msg_id is None and self.error_code)

        return MessageSendResult(
            email_sended,
            self.msg_id,
            None,
            self.error_code,
            self.error_descr
        )

    def get_email_status(self, msg_uuid: str = None, options=None):
        options = options if options else { }
        delivered = False
        error_code = error_descr = None
        url = self.settings['get_email_status_url']
        resp = make_request(url, method='GET', params={
            'format': 'json',
            'api_key': options.get('api_key', self.settings['api_key']),
            'email_id': msg_uuid,
        })

        failed = resp.get('failed_email_id', None)
        if failed:
            for status_dict in failed:
                if msg_uuid in status_dict:
                    error_code = 'error'
                    error_descr = status_dict[msg_uuid]
                    break
        result = resp.get('result', { }).get('statuses', None)
        if result:
            for status_dict in result:
                if status_dict['id'] == msg_uuid:
                    status = status_dict['status']
                    if status == 'ok_delivered':
                        delivered = True
                    else:
                        error_code = status
                        error_descr = self.ERRORS_CHECK_SMS.get(error_code, None)
                    break
        return MessageStatus(delivered, error_code, error_descr, False, False)

    def get_balance(self):
        """
        Только для transactional email-ов:
        POST+JSON /ru/transactional/api/v1/balance.json
        body: { "api_key": "apiKey", "username": "userName"}
        Resp: { "status": "success", "balance": 1234.42, "currency": "USD" }
        """
        pass

    ERRORS_COMMON = {
        'unspecified': 'Тип ошибки не указан',
        'invalid_api_key': 'Указан неправильный ключ доступа к API',
        'access_denied': 'Доступ запрещён',
        'unknown_method': 'Указано неправильное имя метода',
        'invalid_arg': 'Указано неправильное значение одного из аргументов метода',
        'not_enough_money': 'Не хватает денег на счету для выполнения метода',
        'retry_later': 'Временный сбой. Попробуйте ещё раз позднее.',
        'api_call_limit_exceeded_for_api_key': 'Сработало ограничение по вызову методов API в единицу времени',
        'api_call_limit_exceeded_for_ip': 'Сработало ограничение по вызову методов API в единицу времени',
    }
    ERRORS_SEND_SMS = {
        'dest_invalid': 'Доставка невозможна, телефон получателя некорректен',
        'src_invalid': 'Доставка невозможна, аргумент sender (поле «отправитель») некорректен',
        'invalid_arg': 'Доставка невозможна, аргумент sender некорректен (альфа-имя отправителя не зарегистрировано)',
        'has_been_sent': 'SMS данному адресату уже был отправлен. Допустимый интервал между двумя отправками — 1 минута',
        'unsubscribed_globally': 'Адресат глобально отписан от рассылок',
    }
    ERRORS_CHECK_SMS = {
        'not_sent': 'Сообщение пока не отправлено, ждёт отправки. Статус будет изменён после отправки',
        'ok_sent': 'Сообщение отправлено, но статус доставки пока неизвестен. Статус временный и может измениться',
        'ok_delivered': 'Сообщение доставлено. Статус окончательный',
        'err_src_invalid': 'Доставка невозможна, отправитель задан неправильно',
        'err_dest_invalid': 'Доставка невозможна, указан неправильный номер',
        'err_skip_letter': 'Доставка невозможна, т.к. во время отправки был изменён статус телефона, либо телефон был удалён из списка, либо письмо было удалено',
        'err_not_allowed': 'Доставка невозможна, этот оператор связи не обслуживается',
        'err_delivery_failed': 'Доставка не удалась — обычно по причине указания формально правильного, но несуществующего номера или из-за выключенного телефона',
        'err_lost': 'Сообщение было утеряно, отправитель должен переотправить сообщение самостоятельно, т.к. оригинал не сохранился',
        'err_internal': 'внутренний сбой. Необходима переотправка сообщения',
    }


"""
Send email via get parameters:
    Справка: https://www.unisender.com/ru/support/api/messages/sendemail/

https://api.unisender.com/ru/api/sendEmail?format=json&api_key=KEY &email
=TONAME <EMAILTO>&sender_name=
FROMNAME&sender_email=FROMMAIL&subject=SUBJECT
&body=HTMLBODY&list_id=X&attachments[filename1]=FILE1&attachments
[filename2]=FILE2&lang=LANG&error_checking=1&metadata[meta1]=
value1&metadata[meta2]=value2
Resp: {
    "result": 
        [   {"index": 0, "email": "qwe.rty@uio.com", "errors": 
                [  {"code": "unchecked_sender_email", "message": "Неподтвержденный Email отправителя"}
                ]
        }
    ]
}


Send transactional email:
    Справка: https://one.unisender.com/ru/docs/page/get_started
                https://one.unisender.com/ru/docs/page/send

https://one.unisender.com/ru/transactional/api/v1/email/send.json
POST+json
{
  "api_key": "apiKey",
  "username": "userName",
  "message":
  {
    "template_engine" : "simple",
    "template_id" : "template_id",
    "global_substitutions":
    {
      "someVar":"some val"
    },
    "body":
    {
      "html": "<b>Hello {{substitutionName}}</b>",
      "plaintext": "Some plain text"
    },
    "subject": "Example subject",
    "from_email": "emailFrom",
    "from_name": "userName",
    "reply_to": "emailFrom",
    "track_links" : 1,
    "track_read"  : 1,
    "recipients": [
      {
        "email": "emailFrom",
        "substitutions":
        {
          "substitutionName": "substitutionVal",
          "to_name": "Name Surname"
        },
        "metadata":
        {
           "key1" : "val1"
        }
      },
      {
        "email": "bad_email@com",
        "substitutions":
        {
          "substitutionName": "substitutionVal",
          "UNSUB_hash": "Qwcd1789"
        }
      }
    ],
    "metadata":
    {
      "key1" : "val1"
    },
    "headers":
    {
      "X-ReplyTo": "reply@example.com"
    },
    "attachments": [
      {
        "type": "text/plain",
        "name": "myfile.txt",
        "content": "ZXhhbXBsZSBmaWxl" //файл в base64, для использования в HTML должен быть передан как <img src="cid:IMAGECID">
      }
    ],
    "inline_attachments": [
      {
        "type": "image/png",
        "name": "IMAGECID",
        "content": "iVBORw0KGgo" //файл в base64, для использования в HTML должен быть передан как <img src="cid:IMAGECID">
      }
    ],
    "options":
    {
      "unsubscribe_url": "someurl"
    }
  }
}
Resp: {
  "status":"success",
  "job_id":"1ZymBc-00041N-9X",
  "emails":["email@gmail.com"]
}
Resp Err:
{
  "status": "error",
  "code": 123,
  "message": "Error message"
}

{
    "status":"success",
    "job_id":"1ZymBc-00041N-9X",
    "emails":["email@gmail.com"],
    "failed_emails":
    { "email1@gmail.com":"unsubscribed", }
}


Проверка статуса email-а:
    Справка: https://www.unisender.com/ru/support/api/messages/check-email/
https://api.unisender.com/ru/api/checkEmail?format=json&api_key=KEY&email_id=ID1,ID2,ID3
Resp: {
  "result": {
    "statuses": [
      {
        "id": "8219732882",
        "status": "not_sent"
      },
      {
        "id": "8269722886",
        "status": "ok_delivered"
      },
      {
        "id": "8219722800",
        "status": "err_unsubscribed"
      }
    ]
  },
  "failed_email_id": [
    {
      "23": "email_id does not exist"
    },
    {
      "573405639": "passed email_id doesn't match passed api_key"
    }
  ]
}


Send SMS:
    Справка: https://www.unisender.com/ru/support/api/messages/sendsms/
https://api.unisender.com/ru/api/sendSms?format=json&api_key=KEY&phone=TO&sender=FROM&text=TEXT
Resp: {"result": {
    currency 	Трёхбуквенный международный код валюты, в которой посчитана цена сообщения. Валюта совпадает с валютой вашего счёта (RUB, USD, EUR, UAH).
    price 	Цена в валюте currency, число с десятичной точкой.
    sms_id 	Уникальный цифровой код сообщения. Может использоваться для контроля доставки методом checkSms.
} }

"""
