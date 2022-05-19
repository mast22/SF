from typing import Mapping, Iterable
from .. import const as c


class BaseProvider:
    """Базовый класс для всех провайдеров отправки сообщений.
    В каждом подклассе необходимо переопределить методы: send_sms, get_result"""
    PROVIDE = {  # Действия, предоставляемые провайдером
        c.MessageType.SMS: 'send_sms',  # Отправка СМС-сообщения на один или несколько номеров
        c.MessageType.EMAIL: 'send_email',  # Отправка email
        c.MessageType.PUSH: 'send_push',  # Отправка web-push сообщения или android/apple-push
        c.MessageType.VOICE_MESSAGE: 'send_voice_message',  # Отправка голосового-сообщения
        c.MessageType.DIALING: 'send_dialing',  # Отправка дозвона со случайного номера
    }

    DEFAULT_SETTINGS = {
        'login': '',
        'password': '',
        'from': 'fin-service',
        'notification_default_subject': 'Уведомление системы Фин.Услуги',
    }

    def __init__(self, settings: Mapping = None, **kwargs):
        settings = settings if settings else {}
        self.settings = { **self.DEFAULT_SETTINGS, **settings }
        self.msg_id = kwargs.get('msg_id', None)
        self.method = kwargs.get('method', None)
        self.error_code = None
        self.error_descr = None

    def send_mass_message(self,
            msg_type: int = c.MessageType.SMS,
            receivers: Iterable = None,
            text=None,
            subject=None,
            options=None) -> c.MessageSendResult:
        """
        Отправка сообщения определённого типа.
        :param msg_type:
        :param sender:
        :param receivers:
        :param text:
        :param subject:
        :param options:
        :return:
        """
        if not msg_type in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to send sms'.format(self.__class__.__name__))
        if msg_type == c.MessageType.SMS:
            return self.send_sms(receivers=receivers, text=text, options=options)
        elif msg_type == c.MessageType.EMAIL:
            return self.send_email(receivers=receivers, text=text, subject=subject, options=options)
        return getattr(self, self.PROVIDE[msg_type])()

    def send_auth_code(self, phone: str, method: str = 'SMS', code_length: int = 4, options=None):
        """
        Отправляет проверочный код на указанный номер.
        :param phone: телефон получателя
        :param method: метод отправки. Должен быть в CODE_METHODS
            SMS - отправка проверочной смс с кодом
            PHONE_NUMBERS - дозвон, код в последних code_length цифрах номера, с которого звонили
            VOICE - дозвон, код проговаривается в аудиосообщении
        :param code_length: количество символов в проверочном коде
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: NamedTuple формат задан в const.MessageSendResult
        """
        if method in self.PROVIDE:
            return c.MessageSendResult()
        else:
            raise NotImplementedError(
                'Provider {0} doesn\'t allow to send checking code request'.format(self.__class__.__name__))

    def send_notification(self, user_info, message, subject=None, method: str = 'PUSH', options=None):
        """
        Отправляет уведомление пользователю.
        :param user_info:
        :param method:
        :param options:
        :return:
        """
        if not subject:
            subject = self.settings['notification_default_subject']
        if method not in self.PROVIDE:
            raise NotImplementedError(
                'Provider {0} doesn\'t allow to send notification of this type'.format(self.__class__.__name__))

        if method == 'EMAIL':
            return self.send_email(to=user_info.email, text=message, options=options)
        elif method == 'PUSH':
            return self.send_push(to=user_info.phone, text=message, options=options)
        elif method == 'SMS':
            return self.send_sms(to=user_info.phone, text=message, options=options)

    def send_sms(self, to: str = None, receivers: Iterable[str] = None, text: str = None,
            options: Mapping = None) -> c.MessageSendResult:
        """
        Отправляет SMS на указанный номер
        :param to: телефон получателя
        :param receivers: телефоны получателей
            Должен быть задан только один из параметров "to" или "receivers"
        :param text: текст сообщения
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: NamedTuple формат задан в const.MessageSendResult
        """
        assert (to or receivers) and not (to and receivers), 'One of "to" or "receivers" should be set, not both'
        if 'SMS' in self.PROVIDE:
            return c.MessageSendResult()
        else:
            raise NotImplementedError('Provider {0} doesn\'t allow to send sms'.format(self.__class__.__name__))

    def send_push(self, to: str = None, receivers: Iterable[str] = None,
            title: str = '', text: str = '', options: Mapping = None) -> c.MessageSendResult:
        """
        Отправляет push-уведомление на указанный ID
        :param to: uuid получателя
        :param receivers: uuid-ы получателей
            Должен быть задан только один из параметров "to" или "receivers"
        :param title: заголовок сообщения
        :param text: текст сообщения
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: NamedTuple формата: {}.
        """
        if 'PUSH' in self.PROVIDE:
            return c.MessageSendResult()
        else:
            raise NotImplementedError('Provider {0} doesn\'t allow to send push'.format(self.__class__.__name__))

    def send_email(self, to: str = None, receivers: Iterable[str] = None,
            text: str = '', subject='', attachments=None, options: Mapping = None) -> c.MessageSendResult:
        """
        Отправляет сообщение на указанный email
        :param to: email получателя
        :param receivers: email-ы получателей для множественной отправки
            Должен быть задан только один из параметров "to" или "receivers"
        :param text: текст сообщения
        :param subject: заголовок сообщения
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: NamedTuple формата: {}.
        """
        if 'EMAIL' in self.PROVIDE:
            return c.MessageSendResult()
        else:
            raise NotImplementedError('Provider {0} doesn\'t allow to send email'.format(self.__class__.__name__))

    def get_sms_status(self, msg_uuid: str = None, options=None) -> c.MessageStatus:
        """
        Используется для получения результата отправки сообщения методами send_*.
        (Было ли сообщение доставлено пользователю).
        :param msg_uuid: уникальный id сообщения на сервере провайдера
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: Status: named tuple
        """
        if 'SMS' in self.PROVIDE:
            return c.MessageStatus()
        else:
            raise NotImplementedError('Provider {0} doesn\'t allow to get sms status'.format(self.__class__.__name__))

    def get_push_status(self, msg_uuid: str = None, options=None) -> c.MessageStatus:
        """
        Используется для получения результата отправки сообщения методами send_*.
        (Было ли сообщение доставлено пользователю).
        :param msg_uuid: уникальный id сообщения на сервере провайдера
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: Status: named tuple
        """
        if 'PUSH' in self.PROVIDE:
            return c.MessageStatus()
        else:
            raise NotImplementedError('Provider {0} doesn\'t allow to get push status'.format(self.__class__.__name__))

    def get_email_status(self, msg_uuid: str = None, options=None) -> c.MessageStatus:
        """
        Используется для получения результата отправки сообщения методами send_*.
        (Было ли сообщение доставлено пользователю).
        :param msg_uuid: уникальный id сообщения на сервере провайдера
        :param options: доп. опции, специфичные для каждого SMS-провайдера (необязательно)
        :return: Status: named tuple
        """
        if 'EMAIL' in self.PROVIDE:
            return c.MessageSendResult()
        else:
            raise NotImplementedError('Provider {0} doesn\'t allow to get email status'.format(self.__class__.__name__))

    # def get_balance(self) -> c.ProviderBalance:
    #     """
    #     Запрос текущего балланса с сервера SMS-провайдера
    #     """
    #     if 'BALANCE' in self.PROVIDE:
    #         return c.ProviderBalance()
    #     else:
    #         raise NotImplementedError('Provider {0} doesn\'t allow to get balance'.format(self.__class__.__name__))

    # def ping(self) -> bool:
    #     """
    #     Пингует провайдера на доступность.
    #     Реализация по умолчанию проверяет, что текущий балланс больше 1 копейки
    #     """
    #     balance = self.get_balance()
    #     return balance.money and balance.money >= 0.01
