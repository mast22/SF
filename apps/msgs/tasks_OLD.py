from django.conf import settings
from . import const as c
from . import providers
import dramatiq
from dramatiq.rate_limits import BucketRateLimiter
from dramatiq.rate_limits.backends import RedisBackend


redis_backend = RedisBackend()


# Mutex-ы по каждому провайдеру. Переделать в генерацию по настройкам в settings.
DISTRIBUTED_MUTEX_SMSC = BucketRateLimiter(redis_backend, 'distributed-mutex-smsc', limit=100, bucket=1_000)
DISTRIBUTED_MUTEX_SMSINT = BucketRateLimiter(redis_backend, 'distributed-mutex-smsint', limit=100, bucket=1_000)
DISTRIBUTED_MUTEX_SMTP = BucketRateLimiter(redis_backend, 'distributed-mutex-smtp', limit=100, bucket=1_000)
DISTRIBUTED_MUTEX_UNISENDER = BucketRateLimiter(redis_backend, 'distributed-mutex-unisender', limit=100, bucket=1_000)


# TODO: Одно и то же везде - переделать в Factory, как время будет.
@dramatiq.actor(max_retries=5, min_backoff=15_000, max_backoff=60_000, time_limit=10_000, max_age=600_000)
def smsc_ru_task(msg_type, msg_source, msg_data, *args, **kwargs):
    return send_message_limiter(providers.SmscProvider, DISTRIBUTED_MUTEX_SMSC,
        msg_type, msg_source, msg_data, *args, **kwargs)


@dramatiq.actor(max_retries=5, min_backoff=15_000, max_backoff=60_000, time_limit=10_000, max_age=600_000)
def smsint_ru_task(msg_type, msg_source, msg_data, *args, **kwargs):
    return send_message_limiter(providers.SmsintProvider, DISTRIBUTED_MUTEX_SMSINT,
        msg_type, msg_source, msg_data, *args, **kwargs)


@dramatiq.actor(max_retries=5, min_backoff=15_000, max_backoff=60_000, time_limit=10_000, max_age=600_000)
def smtp_task(msg_type, msg_source, msg_data, *args, **kwargs):
    return send_message_limiter(providers.SmtpEmailProvider, DISTRIBUTED_MUTEX_SMTP,
        msg_type, msg_source, msg_data, *args, **kwargs)


@dramatiq.actor(max_retries=5, min_backoff=15_000, max_backoff=60_000, time_limit=10_000, max_age=600_000)
def unisender_task(msg_type, msg_source, msg_data, *args, **kwargs):
    return send_message_limiter(providers.UnisenderProvider, DISTRIBUTED_MUTEX_UNISENDER,
        msg_type, msg_source, msg_data, *args, **kwargs)


def send_message_limiter(provider_class, mutex, msg_type, msg_source, msg_data, *args, **kwargs):
    """Отправлять не более LIMIT сообщений в секунду, для чего используется mutex."""
    with mutex.acquire(raise_on_failure=False) as acquired:
        if acquired:
            return send_message_real(provider_class, msg_type, msg_source, msg_data, *args, **kwargs)
        else:
            raise dramatiq.RateLimitExceeded


def send_message_real(provider_class, msg_type, msg_source, msg_data, *args, **kwargs):
    """Обобщённая отправка сообщения выбранным провайдером.
    По msg_type разделяет на конкретную отправку и вызывает соотв. функцию."""
    send_method_name = select_sending_method(msg_type, msg_source, provider_class)
    resp = {}
    return resp


def select_sending_method(msg_type, msg_source, provider):
    # FIXME: Переделать, чтобы выбиралось откуда-нибудь автоматически, или перенести в настройки.
    ALLOWED_MESSAGE_TYPES = {
        c.MessageSource.AUTH_CODE: {
            c.MessageType.SMS: 'send_sms',
            c.MessageType.DIALING: 'send_dialing',
        },
        c.MessageSource.NOTIFICATION: {
            c.MessageType.PUSH: 'send_push',
            c.MessageType.EMAIL: 'send_email',
            c.MessageType.TELEGRAM: 'send_telegram_message',
        }
    }
    if msg_type not in provider.PROVIDE:
        raise KeyError(f'Provider {provider.name} does not support message type: {msg_type}')
    send_method_name = ALLOWED_MESSAGE_TYPES.get(msg_source, {}).get(msg_type, None)
    if send_method_name is None:
        raise ValueError(f'There is not method for msg_source: {msg_source} and msg_type: {msg_type}')
    return send_method_name




def send_auth_code_real(requests, provider_class, provider_name):
    """Отправляет проверочные коды множеству пользователей
    :param requests: Запросы celery-batches
    :param provider_class: класс, отвечающий непосредственно за отправку
    """
    kwargs = tuple(req.args[0] for req in requests if req.args and isinstance(req.args[0], dict))
    auth_data = {data['temp_token']: data.get('options', None)
            for data in kwargs if data and data['temp_token'] is not None}

    provider = provider_class(u.get_provider_settings(provider_name))
    temp_tokens = TempToken.objects.filter(key__in=auth_data.keys())

    for temp_token in temp_tokens:
        options = auth_data[temp_token.key]
        phone = temp_token.phone_number
        try:
            msg_result = provider.send_auth_code(phone, options=options)
        except ProviderError as err:
            logger.error(f'send_auth_code_real. Error: {err}')
            raise

        temp_token.code = msg_result.code
        temp_token.provider_uuid = msg_result.message_id
        if msg_result.sent:
            temp_token.send_status = c.SendStatus.SENT
        else:
            temp_token.send_status = c.SendStatus.ERROR
            logger.warning(f'Auth message to {temp_token.phone_number} (id:{temp_token.user_id})'
                           f' was not sent. Error: {msg_result.decision_code} {msg_result.error_description}')
        temp_token.save(update_fields=('send_status', 'code', 'provider_uuid'))
    return True


def send_web_push(receiver,
        notification_type: str,
        format_data: dict or None=None,
        data: dict or None=None,
        uuid=None,
        options=None):
    """
    Асинхронная отправка push-нотификации пользователю
    :param apps.users.models.User receiver: получатель сообщения
    :param str notification_type: тип - один из msgs.const.NOTIFICATION
    :param dict format_data: данные для форматирования сообщения (должны соотв. msgs.const.NOTIFICATION)
    :param dict or None data: дополнительные данные (должны соотв. msgs.const.NOTIFICATION)
    :param int or str or None uuid: ID, уникальный для группы одинаковых сообщений (будут отправлены вместе)
    :param dict or None options: дополнительные опции, могут быть специфичны для провайдера
    :return: None
    """
    options = options if options else {}
    data = data if data else {}
    msg = c.NOTIFICATIONS[notification_type]
    options = options if options else {}
    use_celery = options.pop('use_celery', getattr(settings, 'USE_CELERY', True))
    provider_task = u.get_celery_task('NOTIFICATION', 'send_push', receiver.push_device_type)

    data['msg_type'] = msg['msg_type']

    msg_data = {
        'to': receiver.push_token,
        'data': data,
    }
    if 'subject' in msg:
        msg_data['subject'] = msg['subject'].format(**format_data)

    if 'text' in msg:
        msg_data['text'] = msg['text'].format(**format_data)

    if uuid:
        msg_data['uuid'] = uuid
    if options:
        msg_data['options'] = options
    if use_celery:
        provider_task.delay(msg_data)
    else:
        provider_task.apply(args=(msg_data,))


def send_email():
    pass


def send_telegram_message():
    pass



