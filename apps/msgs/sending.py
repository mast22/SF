from django.conf import settings

from apps.users.models import TempToken
from .exceptions import ProviderError
from . import utils as u
from . import const as c
from .providers.base_provider import BaseProvider
from . import logger



def send_auth_code_real(msg_data, msg_type, provider_method, options=None, *args, **kwargs):
    """Отправляет проверочный код заданному пользователю.
    :param(dict) msg_data: данные сообщения (временный токен, опции)
    :param(str) msg_type: тип отправляемого сообщения,
    :param(callable) provider_method: метод, отвечающий непосредственно за отправку
    """
    logger.warning(f'send_auth_code_real. msg_data: {msg_data}, msg_type: {msg_type}, method: {provider_method}')
    temp_token_key = msg_data.get('temp_token', None)
    if not temp_token_key:
        raise ValueError(f'There is no temp_token key in message data: {msg_data}')
    temp_token = TempToken.objects.get_token(temp_token_key)
    code_length = options.get('code_length', c.DEFAULT_CODE_LENGTH)
    try:
        resp = provider_method(temp_token.phone, msg_type, code_length=code_length, options=msg_data.get('options', {}))
    except Exception as err:
        logger.error(f'Error in {provider_method}: {err}', stack_info=True)
        return None

    temp_token.code = resp.code
    temp_token.provider_uuid = resp.message_id
    if resp.sent:
        temp_token.send_status = c.SendStatus.SENT
    else:
        temp_token.send_status = c.SendStatus.ERROR
        logger.warning(f'Auth message to {temp_token.phone} (id:{temp_token.user_id})'
                       f' was not sent. Error: {resp.decision_code} {resp.error_description}')
    temp_token.save(update_fields=('send_status', 'code', 'provider_uuid'))
    return None




def send_notification_real(msg_data, msg_type, provider_method, options=None, *args, **kwargs):
    """Отправляет уведомление заданному пользователю.
    :param(dict) msg_data: данные сообщения (временный токен, опции)
    :param(str) msg_type: тип отправляемого сообщения,
    :param(callable) provider_method: метод, отвечающий непосредственно за отправку
    """
    receiver = msg_data.get('receiver', None)
    if not receiver:
        raise ValueError(f'There is no receiver in message data: {msg_data}')
    pass

