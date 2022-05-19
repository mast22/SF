from django.conf import settings
from . import const as c
from . import utils as u
from . import logger


def send_auth_code(temp_token, send_type=c.MessageType.SMS, options=None):
    """Асинхронная отправка проверочного кода пользователю"""
    logger.debug(f'send_auth_code {send_type}. Token: {temp_token} options: {options}')

    options = options if options else {}
    use_redis = options.pop('use_redis', getattr(settings, 'USE_REDIS', True))
    provider_task = u.select_task(temp_token.user, msg_source=c.MessageSource.AUTH_CODE, msg_type=send_type)

    msg_data = {
        'temp_token': temp_token.key,
        'options': options,
    }
    logger.info(f'send_auth_code. provider_task: {provider_task}, data: {msg_data}')
    if use_redis:
        provider_task.send(msg_data=msg_data, msg_source=c.MessageSource.AUTH_CODE, msg_type=send_type)
    else:
        provider_task(msg_data=msg_data, msg_source=c.MessageSource.AUTH_CODE, msg_type=send_type)


def send_notification(user, msg_type, format_data=None, data=None, options=None):
    """"""
    logger.debug(f'send_notification {msg_type}. User: {user}, format_data: {format_data} data: {data}, options: {options}')
    return None
