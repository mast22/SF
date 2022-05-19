from apps.common.utils import generate_random_uuid
from apps.msgs.providers.base_provider import BaseProvider
from apps.common.utils import generate_code
from apps.msgs.exceptions import ProviderKeyError # , ProviderError
from apps.msgs.const import MessageStatus, MessageSendResult, ProviderBalance, MessageType, SendStatus
from .models import DummyMessage
from . import logger


class DummyProvider(BaseProvider):
    """Фейковый провайдер. Сохраняет отправляемые сообщения в специальную таблицу."""
    DEFAULT_SETTINGS = {
        'email_from_name': 'Oppen',
        'email_from': 'admin@oppen.ru',
        'from': 'oppen',
        'notification_default_subject': 'Уведомление системы oppen',
        'code_message': 'Проверочный код: {code}'
    }

    def send_mass_message(self, msg_type: int=MessageType.SMS,
                     sender: str=None, receivers=None,
                     text=None, subject=None, data=None,
                     options=None) -> MessageSendResult:
        if not receivers:
            raise ProviderKeyError('At least one receivier should be set, got none')
        status = options.get('status', SendStatus.SENT)
        uuid = generate_random_uuid()
        for receiver in receivers:
            DummyMessage.objects.create(
                type=msg_type,
                uuid=uuid,
                status=status,
                sender=sender if sender else 'system',
                receiver=receiver,
                subject=subject if subject else '',
                message=text if text else '',
                data=data,
            )
        sent = status in (SendStatus.SENT, SendStatus.RECEIVED)
        logger.warning(f'DummyProvider.send_mass_message. msg_type:{msg_type}, receivers: {receivers}, text: {text},'
                     f'subject: {subject}, data: {data}, options: {options}')
        return MessageSendResult(
            sent=sent,
            message_id=uuid,
            code=None,
            error_code=None if sent else 'error',
            error_description=None if sent else 'Error Message String'
        )

    def send_sms(self, to=None, receivers=None, text='', options=None) -> MessageSendResult:
        if MessageType.SMS not in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to send sms'.format(self.__class__.__name__))

        options = options if options else {}
        if to:
            return self.send_mass_message(msg_type=MessageType.SMS, receivers=[to],
                                          text=text, options=options)
        else:
            return self.send_mass_message(msg_type=MessageType.SMS, receivers=receivers,
                                          text=text, options=options)

    def send_auth_code(self, phone, method='CODE_PHONE_NUMBERS', code_length=4, options=None):
        options = options if options else {}
        code = generate_code(code_length)
        message = options.get('code_message', self.DEFAULT_SETTINGS['code_message']) \
                        .format(code=code)
        status = options.get('status', SendStatus.SENT)
        msg = DummyMessage.objects.create(
            type=MessageType.SMS,
            status=status,
            receiver=phone,
            message=message
        )
        sent = status in (SendStatus.SENT, SendStatus.RECEIVED)
        logger.warning(f'DummyProvider.send_auth_code. phone: {phone}, method: {method}, code_length: {code_length},'
                     f'options: {options}')
        return MessageSendResult(
            sent=sent,
            message_id=msg.uuid,
            code=code,
            error_code=None if sent else 'error',
            error_description=None if sent else 'Error Message String'
        )

    def send_push(self, to=None, receivers=None, subject='', text='', data=None, options=None) -> MessageSendResult:
        if MessageType.PUSH not in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to send push'.format(self.__class__.__name__))
        options = options if options else {}

        if data:
            subject = data['subject'] if 'subject' in data else subject
            text = data['text'] if text in data else text

        if to:
            receivers = [to]
        return self.send_mass_message(msg_type=MessageType.PUSH, receivers=receivers,
            subject=subject, text=text, data=data, options=options)

    def send_email(self, to=None, receivers=None, text='', subject='', attachments=None, options=None) -> MessageSendResult:
        if MessageType.EMAIL not in self.PROVIDE:
            raise NotImplementedError('Provider {0} is not\'t allowed to send email'.format(self.__class__.__name__))

        options = options if options else {}
        receivers = receivers if receivers else [to]
        status = options.get('status', SendStatus.SENT)
        uuid = generate_random_uuid()
        sender = '{0} <{1}>'.format(
            options.get('from_name', self.settings['email_from_name']),
            options.get('from_email', self.settings['email_from'])
        )
        for r in receivers:
            msg = DummyMessage.objects.create(
                type=MessageType.EMAIL,
                uuid=uuid,
                status=status,
                sender=sender,
                receiver=r,
                subject=subject,
                message=text
            )
        sent = status in (SendStatus.SENT, SendStatus.RECEIVED)
        logger.warning(f'DummyProvider.send_email. receivers: {receivers}, text: {text},'
                     f'subject: {subject}, attachments: {attachments}, options: {options}')
        return MessageSendResult(
            sent=sent,
            message_id=uuid,
            code=None,
            error_code=None if sent else 'error',
            error_description=None if sent else 'Error Message String'
        )

    def get_sms_status(self, msg_uuid: str=None, options=None) -> MessageStatus:
        if 'SMS' not in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to get sms status'.format(self.__class__.__name__))
        return MessageStatus()

    def get_push_status(self, msg_uuid: str=None, options=None) -> MessageStatus:
        if 'PUSH' not in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to get push status'.format(self.__class__.__name__))
        return MessageStatus()

    def get_email_status(self, msg_uuid: str=None, options=None) -> MessageStatus:
        if 'EMAIL' not in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to get email status'.format(self.__class__.__name__))
        return MessageSendResult()

    def get_balance(self) -> ProviderBalance:
        if 'BALANCE' in self.PROVIDE:
            raise NotImplementedError('Provider {0} doesn\'t allow to get balance'.format(self.__class__.__name__))
        return ProviderBalance()

    def ping(self) -> bool:
        balance = self.get_balance()
        return balance.money and balance.money >= 0.01
