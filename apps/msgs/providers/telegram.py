from .base_provider import BaseProvider
from .. import const as c


class TelegramProvider(BaseProvider):
    DEFAULT_SETTINGS = {
        'login': '',
        'password': '',
        'from': 'fin-service',
        'notification_default_subject': 'Уведомление системы Фин.Услуги',
    }
    PROVIDE = {
        c.MessageType.TELEGRAM: 'send_telegram_message',
    }

    def send_telegram_message(self, to: str, message: str='', options=None):

        return c.MessageSendResult(False, None, None, None, None)

