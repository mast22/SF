from apps.common.utils import generate_code
from .base_provider import BaseProvider
from ..const import MessageStatus, MessageSendResult, ProviderBalance, MessageType
from ..utils import make_request, convert_to_xml
from ..exceptions import ProviderKeyError


class SmsintProvider(BaseProvider):
    """Provider class for smsint.ru"""
    # TODO: Возможно, придётся переделать на использование xml-api, т.к. не все методы доступны через JSON
    # TODO: написать в ТП, когда будут логни/пароль, возможно, метод есть, но нет описания в справке!
    # Например, нельзя получить статус доставки SMS на номер
    PROVIDE = {
        MessageType.SMS: 'send_sms',
        MessageType.DIALING: 'send_auth_code',
    }

    DEFAULT_SETTINGS = {
        'base_url': 'https://lcab.smsint.ru/lcabApi',
        'send_sms_url': 'https://lcab.smsint.ru/API/XML/send.php',
        'get_sms_status_url': 'https://lcab.smsint.ru/API/XML/report.php',
        'get_balance_url': 'https://lcab.smsint.ru/API/XML/balance.php',
        'check': 0,  # В доках не понятно, что именно означает параметр
        'channel': None,  # No, 0, 1, 2
        'discountID': None,  # ID акции
        # Обязательные параметры:
        'sms_from': None,  # Имя отправителя SMS
        'login': None,
        'password': None,
    }

    def __init__(self, settings, **options):
        super(SmsintProvider, self).__init__(settings, **options)
        self.error_code = options.get('error_code', None)
        self.error_descr = options.get('error_descr', None)
        self.time = options.get('time', None)
        self.phone = options.get('phone', None)

    def send_sms(self, to=None, receivers=None, text=None, options=None):
        options = options if options else { }
        url = self.settings['send_sms_url']
        data = convert_to_xml({
            'login': options.get('login', self.settings['login']),
            'password': options.get('password', self.settings['password']),
            'action': 'send',
            'text': text,
            'source': options.get('sms_from', self.settings['sms_from']),
            'to': { 'number': to },
            'check': options.get('check', self.settings['check']),
            'channel': options.get('channel', self.settings['channel']),
            'discountID': options.get('discountID', self.settings['discountID']),
        })
        resp = make_request(url, method='POST', data=data, req_type='XML', resp_type='XML')
        resp_data = resp.get('data', { })

        # from pprint import pprint
        # print('Response:')
        # pprint(resp)

        self.error_code = int(resp_data.get('code', 0))
        is_sent = self.error_code == 1
        self.error_descr = resp_data.get('descr', None)
        self.msg_id = resp_data.get('smsid', None)
        return MessageSendResult(is_sent, self.msg_id, None, self.error_code, self.error_descr)

    # def send_auth_code(self, phone=None, method='SMS', code_length=6, options=None):
    def send_auth_code(self, phone=None, method='SMS', code_length=6, code_message=None, options=None):
        """Дозвон на тф номер с получением последних 6 цифр в качестве кода"""
        phone = phone if phone else self.phone
        self.phone = phone

        method = method if method else self.method
        if method == 'SMS':
            code = generate_code(code_length)
            text = options.get('code_message', self.settings['code_message']).format(code=code)
            resp = self.send_sms(to=phone, text=text, options=options)
            return resp._replace(code=code)
        else:
            raise ProviderKeyError('Method {0} is not supported'.format(method))

    def get_status(self, msg_uid=None, options=None) -> MessageStatus:
        options = options if options else { }
        url = self.settings['send_sms_url']
        msg_id = msg_uid if msg_uid else self.msg_id
        if not msg_id:
            raise ProviderKeyError('There is no msg_uuid available to check')
        data = convert_to_xml({
            'login': options.get('login', self.settings['login']),
            'password': options.get('password', self.settings['password']),
            'sms_id': msg_id,
        })
        resp = make_request(url, method='POST', data=data, req_type='XML')
        resp_data = resp.get('data', { })

        # from pprint import pprint
        # print('Response:')
        # pprint(resp)

        error_code = resp_data.get('code', 0)
        error_descr = resp_data.get('descr', None)
        details = resp_data.get('detail', { })
        delivered = bool(details.get('delivered', { }).get('number', False))
        need_recheck = bool(details.get('waiting', { }).get('number', None)
                            or (details.get('enqueued', { }).get('number', None))
                            or (details.get('process', { }).get('number', None)))
        return MessageStatus(delivered, error_code, error_descr, need_recheck, False)

    def get_balance(self, options=None):
        options = options if options else { }
        url = self.settings['send_sms_url']
        data = convert_to_xml({
            'login': options.get('login', self.settings['login']),
            'password': options.get('password', self.settings['password']),
        })
        resp = make_request(url, method='POST', data=data, req_type='XML')
        resp_data = resp.get('data', { })

        # from pprint import pprint
        # print('Response:')
        # pprint(resp)

        error_code = resp_data.get('code', 0)
        error_descr = resp_data.get('descr', None)
        balance = float(resp_data.get('account', 0))
        return ProviderBalance(balance, error_code, error_descr)


"""
Справка:
    https://smsint.ru/integration/xml/

Sms Send:
https://lcab.smsint.ru/lcabApi/sendSms.php?login=ЛОГИН&password=ПАРОЛЬ&txt=привет&to=89010003333
Resp Success:
array(
    "code" => 1,
    "descr" => "Операция успешно завершена",
    "smsid" => "ID рассылки, который присвоили вы, или наша система в случае если вы не передали свой smsid",
    "datetime" => "Время отправки в MySQL формате",
    "allRecivers" => "Количество абонентов в рассылке",
    "colSendAbonent" => "Количество тех, кто получит смс",
    "colNonSendAbonent" => "Количество тех, кто смс не получит",
    "priceOfSending" => "Стоимость рассылки",
    "colsmsOfSending" => "Количество смс в рассылке",
    "price" => "Стоимость одной смс"
)
Resp Failure:
array(
    "code" => "Код ошибки",
    "descr" => "Описание ошибки"
)

Send via xml:   https://lcab.smsint.ru/API/XML/send.php
    <?xml version='1.0' encoding='UTF-8'?>
        <data>
            <login>LOGIN</login>
            <password>PASSWORD</password>
            <action>send</action>
            <text>TEXT</text>
            <source>SOURCE</source>
            <to number='8-923-123-1234'></to>
            <to number='+7(901) 123-45 67'>Текст сообщения 1</to>
            <to number='9011234567'>Текст сообщения 2</to>
            <smsid>SMSID</smsid>
            <datetime>2016-12-31 23:59:59</datetime>
            <regionalTime>1 или 0</regionalTime>
            <vp>7200</vp>
            <stop>1 или 0</stop>
            <channel>ID</channel>
            <allowed_opsos>ID</allowed_opsos>
            <exclude_opsos>ID</exclude_opsos>
    </data>
Response:
    <?xml version='1.0' encoding='UTF-8'?>
    <data>
        <code>CODE</code>
        <descr>DESCR</descr>
        <smsid>SMSID</smsid>
        <datetime>DATETIME</datetime>
        <action>ACTION</action>
        <allRecivers>ALL_RECIEVERS</allRecivers>
        <colSendAbonent>COL_SEND_ABONENT</colSendAbonent>
        <colNonSendAbonent> COL_NON_SEND_ABONENT </colNonSendAbonent>
        <priceOfSending>PRICE_OF_SENDING</priceOfSending>
        <colsmsOfSending>COL_SMS_OF_SENDING</colsmsOfSending>
    </data>


Get Status via xml: https://lcab.smsint.ru/API/XML/report.php
    <?xml version='1.0' encoding='UTF-8'?>
    <data>
        <login>LOGIN</login>
        <password>PASSWORD</password>
        <smsid>SMSID</smsid>
    </data>
Response:
    <?xml version='1.0' encoding='UTF-8'?>
    <data>
        <code>CODE</code>
        <descr>DESCR</descr>
        <detail>
            <delivered>
                <number>79010000000</number>
                <number>79010000001</number>
                <number>79010000002</number>
            </delivered>
            <notDelivered>
                <number>79020000000</number>
            </notDelivered>
            <waiting>
                <number>79030000000</number>
            </waiting>
            <enqueued>
                <number>79040000000</number>
            </enqueued>
            <cancel>
                <number>79050000000</number>
            </cancel>
            <onModer>
                <number>79060000000</number>
            </onModer>
            <process>
                <number>79070000000</number>
            </process>
        </detail>
    </data>


"""
