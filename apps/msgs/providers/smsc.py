from apps.common.utils import generate_code
from .base_provider import BaseProvider
from ..const import MessageStatus, MessageSendResult, ProviderBalance, MessageType
from ..utils import make_request
from ..exceptions import ProviderKeyError


class SmscProvider(BaseProvider):
    PROVIDE = {
        MessageType.SMS: 'send_sms',
        MessageType.DIALING: 'send_dialing',
    }
    DEFAULT_SETTINGS = {
        'send_sms_url': 'https://smsc.ru/sys/send.php',
        'get_sms_status_url': 'https://smsc.ru/sys/status.php',
        'get_balance_url': 'https://smsc.ru/sys/balance.php',
        'translit': 0,  # 0, 1, 2 - Использовать транслит (0 - нет)
        'time': 0,  # Время задержки в сек.
        'fmt': 3,  # Ответ получить в JSON-формате
        'charset': 'utf-8',
        'code_message': 'Ваш проверочный код: {code}',  # Текст сообщения для проверочного кода
        # Обязательные параметры:
        'sms_from': None,  # Имя отправителя SMS
        'login': None,
        'password': None,
    }

    def __init__(self, settings: dict, **options):
        super(SmscProvider, self).__init__(settings, **options)
        self.call_code = None

    def send_sms(self, to=None, receivers=None, text=None, options=None):
        options = options if options else { }
        assert (to or receivers) and not (to and receivers), 'One of "to" or "receivers" should be set, not both'
        if to:
            receivers = (to,)
        url = self.settings['send_sms_url']
        params = {
            'phones': receivers,
            'mes': text,
            'login': options.get('login', self.settings['login']),
            'psw': options.get('password', self.settings['password']),
            'sender': options.get('from', self.settings['sms_from']),
            'time': options.get('time', self.settings['time']),
            'charset': options.get('charset', self.settings['charset']),
            'fmt': options.get('fmt', self.settings['fmt']),
        }
        if 'call' in options:
            params['call'] = options['call']
        resp = make_request(url, method='POST', params=params)

        self.phone = receivers
        self.error_code = int(resp.get('error_code', 0))
        self.error_descr = resp.get('error', None)
        self.msg_id = resp.get('id', None)
        self.call_code = resp.get('code', None)

        return MessageSendResult(
            not self.error_code,
            self.msg_id,
            self.call_code,
            self.error_code,
            self.error_descr
        )

    # def send_auth_code(self, phone=None, msg_type=MessageType.SMS, code_length=4, options=None):
    def send_auth_code(self, phone=None, msg_type=MessageType.SMS, code_length=4, code_message=None, options=None):
        """Дозвон на тф номер с получением последних 6 цифр в качестве кода"""
        options = options if options else {}

        if msg_type == MessageType.DIALING:
            options['call'] = 1
            return self.send_sms(to=phone, text='code', options=options)

        elif msg_type == MessageType.SMS:
            code = generate_code(code_length)
            code_message = code_message if code_message else self.settings['code_message']
            text = code_message.format(code=code)
            resp = self.send_sms(to=phone, text=text, options=options)
            return resp._replace(code=code)
        else:
            raise ProviderKeyError('Method {0} is not supported'.format(msg_type))

    def get_sms_status(self, msg_uuid=None, options=None):
        options = options if options else { }
        url = self.settings['get_sms_status_url']
        sms_id = msg_uuid if msg_uuid else self.msg_id
        if not sms_id:
            raise ProviderKeyError('There is no msg_uuid available to check')
        resp = make_request(url, method='POST', params={
            'login': options.get('login', self.settings['login']),
            'psw': options.get('password', self.settings['password']),
            'phone': options.get('phone', self.phone),
            'id': sms_id,
            'all': options.get('all', 1),  # 0,1,2 - Нужен ли расширенный формат ответа
            'del': options.get('del', 0),  # Удалить отправленное сообщение с сервера smsc
            'charset': options.get('charset', 'utf-8'),
            'fmt': 3  # Ответ в JSON-формате
        })

        # from pprint import pprint
        # print('Response:')
        # pprint(resp)

        error_code = resp.get('error_code', None)
        delivered = int(resp.get('status', 0)) == 1
        error_descr = resp.get('err', '') if error_code is None \
            else resp.get('error', '')

        return MessageStatus(delivered, error_code, error_descr, False, False)

    def get_balance(self, options=None):
        options = options if options else { }
        url = self.settings['get_balance_url']
        resp = make_request(url, method='POST', params={
            'login': self.settings['login'],
            'psw': self.settings['password'],
            'fmt': 3  # Ответ в JSON-формате
        })

        # from pprint import pprint
        # print('Response:')
        # pprint(resp)

        error_code = resp.get('error_code', None)
        error_descr = resp.get('error', '')
        balance = resp.get('balance')
        return ProviderBalance(balance, error_code, error_descr)

    ERRORS_COMMON = {
        1: 'Ошибка в параметрах',
        2: 'Неверный логин или пароль (или IP-адрес)',
        3: 'Недостаточно средств на счете Клиента',
        4: 'IP-адрес временно заблокирован из-за частых ошибок в запросах',
        5: 'Неверный формат даты',
        6: 'Сообщение запрещено (по тексту или по имени отправителя)',
        7: 'Неверный формат номера телефона',
        8: 'Сообщение на указанный номер не может быть доставлено',
        9: 'Отправка более одного одинакового запроса на передачу SMS-сообщения либо более пяти одинаковых запросов на получение стоимости сообщения в течение минуты, либо более 15 одновременных запросов к серверу',
    }

    MESSAGE_STATUSES = {
        -3: 'Сообщение не найдено: Возникает, если для указанного номера телефона и ID сообщение не найдено',
        -2: 'Остановлено: Возникает у сообщений из рассылки, которые не успели уйти оператору до момента временной остановки данной рассылки на странице Рассылки и задания',
        -1: 'Ожидает отправки: Если при отправке сообщения было задано время получения абонентом, то до этого времени сообщение будет находиться в данном статусе, в других случаях сообщение в этом статусе находится непродолжительное время перед отправкой на SMS-центр',
        0: 'Передано оператору: Сообщение было передано на SMS-центр оператора для доставки',
        1: 'Доставлено: Сообщение было успешно доставлено абоненту',
        2: 'Прочитано: Сообщение было прочитано (открыто) абонентом. Данный статус возможен для e-mail-сообщений, имеющих формат html-документа',
        3: 'Просрочено: Возникает, если время "жизни" сообщения истекло, а оно так и не было доставлено получателю, например, если абонент не был доступен в течение определенного времени или в его телефоне был переполнен буфер сообщений',
        4: 'Нажата ссылка: Сообщение было доставлено, и абонентом была нажата короткая ссылка, переданная в сообщении. Данный статус возможен при включенных в настройках опциях "Автоматически сокращать ссылки в сообщениях" и "отслеживать номера абонентов"',
        20: 'Невозможно доставить: Попытка доставить сообщение закончилась неудачно, это может быть вызвано разными причинами, например, абонент заблокирован, не существует, находится в роуминге без поддержки обмена SMS, или на его телефоне не поддерживается прием SMS-сообщений',
        22: 'Неверный номер: Неправильный формат номера телефона',
        23: 'Запрещено: Возникает при срабатывании ограничений на отправку дублей, на частые сообщения на один номер (флуд), на номера из черного списка, на запрещенные спам фильтром тексты или имена отправителей (Sender ID)',
        24: 'Недостаточно средств: На счете Клиента недостаточная сумма для отправки сообщения',
        25: 'Недоступный номер: Телефонный номер не принимает SMS-сообщения, или на этого оператора нет рабочего маршрута',
    }

    MESSAGE_ERROR_STATUSES = {
        0: 'Нет ошибки',
        1: 'Абонент не существует',
        6: 'Абонент не в сети',
        11: 'Нет услуги SMS',
        12: 'Ошибка в телефоне абонента',
        13: 'Абонент заблокирован',
        21: 'Аппарат абонента не поддерживает работу с данной услугой (сервисом)',
        200: 'Виртуальная отправка (режим тестирования)',
        219: 'Замена sim-карты абонентом',
        220: 'Переполнена очередь у оператора',
        239: 'Запрещенный ip-адрес отправителя',
        240: 'Абонент занят (при передаче голосового сообщения абоненту)',
        241: 'Ошибка конвертации или переданы не все части SMS-сообщения',
        242: 'Зафиксирован автоответчик при отправке голосового сообщения',
        243: 'Не заключен договор',
        244: 'Рассылка запрещена',
        245: 'Статус не получен',
        246: 'Ограничение по времени',
        247: 'Превышен лимит сообщений',
        248: 'Нет маршрута (нет доступного SMS-шлюза для указанного номера)',
        249: 'Неверный формат номера',
        250: 'Номер запрещен настройками',
        251: 'Превышен суточный лимит сообщений на один номер',
        252: 'Номер запрещен',
        253: 'Запрещено спам-фильтром',
        254: 'Незарегистрированный sender id: попытка отправки сообщения от незарегистрированного имени отправителя',
        255: 'Оператор отклонил сообщение без указания точного кода ошибки',
    }


"""
Send Query:
https://smsc.ru/sys/send.php?login=<login>&psw=<password>&phones=<phones>&mes=<message>
success resp: {
    "id": <id>,
    "cnt": <n>
}
error resp: {
    'error_code': int,
    'error': text,
    'id': ID сообщения (при ошибках 3,6,7,8)
}

Status Query:
https://smsc.ru/sys/status.php?login=<login>&psw=<password>&phone=<phone>&id=<sms_id>
Success Response:
{
    "status": <status>,
    "last_date": "<last_date>",
    "last_timestamp": <last_timestamp>,
    "err": <err>
}
Error Response:
{
    "error": "описание",
    "error_code": N
}


"""
