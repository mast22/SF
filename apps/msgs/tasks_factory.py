from django.conf import settings
import dramatiq
from dramatiq.rate_limits import BucketRateLimiter
from dramatiq.rate_limits.backends import RedisBackend
from . import const as c
from .sending import send_auth_code_real, send_notification_real
from . import utils as u
from . import logger


# MESSAGES_SETTINGS = {
#     c.MessageSource.AUTH_CODE: {
#         c.MessageType.SMS: {'method': 'send_auth_code', 'provider': 'smsc.ru'},
#         c.MessageType.DIALING: {'method': 'send_dialing', 'provider': 'smsc.ru'},
#     },
#     c.MessageSource.NOTIFICATION: {
#         c.MessageType.PUSH: {
#             'method': 'send_push',
#             'choose_provider_by': 'apps.msgs.utils.push_provider_selector',
#             'providers': {
#                 'APNS': 'apns',
#                 'FCM': 'fcm',
#                 'WEB': 'dummy_provider',
#                 'DUMMY': 'dummy_provider',
#             }
#         },
#         c.MessageType.EMAIL: {'method': 'send_email', 'provider': 'unisender.com'},
#         c.MessageType.TELEGRAM: {
#             'method': 'send_telegram_message',
#             'provider': 'telegram-client',
#         }
#     }
# }


class TasksFactory:
    """
    Создаёт конкретный таск для отправки сообщений в зависимости от переданных параметров.
    """
    def create_all_tasks(self, mutex_backend_class=RedisBackend):
        msgs_providers = getattr(settings, 'MESSAGES_PROVIDERS', {})
        mutex_backend = self.instantiate_mutex_backend(mutex_backend_class)
        provider_tasks = {}
        for provider_name, provider_item in msgs_providers.items():
            task = self.create_task(provider_name, provider_item, mutex_backend)
            provider_tasks[provider_name] = task
        return provider_tasks

    def create_task(self, provider_name, provider_item, mutex_backend):
        """Создаёт конкретный таск на базе настроек"""
        provider_mutex = self.create_mutex(provider_name, provider_item, mutex_backend)
        method = self.create_message_task_function(provider_name, provider_mutex)
        broker_options = self.get_broker_options(provider_item)
        task_name = u.get_task_name(provider_name)
        method.__name__ = task_name
        task = dramatiq.actor(method, queue_name='default', **broker_options)
        return task

    def get_broker_options(self, provider_item):
        return {**c.DEFAULT_TASK_PARAMETERS, **provider_item.get('task_settings', {})}

    def create_message_task_function(self, provider_name, provider_mutex):
        def _task(msg_data, msg_type, msg_source, *args, **kwargs):
            provider_item = getattr(settings, 'MESSAGES_PROVIDERS', {}).get(provider_name, None)
            provider_class, provider_settings = u.get_provider_class(provider_item)
            return send_message_limiter(provider_mutex, msg_data, msg_type, msg_source,
                   provider_class, provider_settings, *args, **kwargs)
        logger.debug(f'Create task for {provider_name}')
        return _task

    def create_mutex(self, provider_name, provider_settings, mutex_backend):
        mutex_name = f'distributed-mutex-{provider_name}'
        distributed_mutex = BucketRateLimiter(mutex_backend, mutex_name, limit=100, bucket=1_000)
        return distributed_mutex

    def instantiate_mutex_backend(self, backend_class):
        url = getattr(settings, 'DRAMATIQ_BROKER', {}).get('OPTIONS', {}).get('url', None)
        if url:
            backend = backend_class(url=url)
        else:
            backend = backend_class()
        return backend


def send_message_limiter(mutex, msg_data, msg_type, msg_source, provider_class, provider_settings, *args, **kwargs):
    """Отправлять не более LIMIT сообщений в секунду, для чего используется mutex."""
    if mutex:
        with mutex.acquire(raise_on_failure=False) as acquired:
            if acquired:
                return send_message_wrapper(msg_data, msg_type, msg_source, provider_class, provider_settings,
                       *args, **kwargs)
            else:
                raise dramatiq.RateLimitExceeded
    else:
        return send_message_wrapper(msg_data, msg_type, msg_source, provider_class, provider_settings,
               *args, **kwargs)


def send_message_wrapper(msg_data, msg_type, msg_source,  provider_class, provider_settings, *args, **kwargs):
    """Обобщённая отправка сообщения выбранным провайдером.
    По msg_type разделяет на конкретную отправку и вызывает соотв. функцию."""
    provider_object = provider_class(settings=provider_settings)
    provider_method_name, options = u.select_sending_method(msg_source, msg_type)
    provider_method = getattr(provider_object, provider_method_name)

    SEND_MESSAGE_METHOD = {
        c.MessageSource.AUTH_CODE: send_auth_code_real,
        c.MessageSource.NOTIFICATION: send_notification_real,
    }
    sending_method = SEND_MESSAGE_METHOD.get(msg_source, None)
    if sending_method is None:
        raise ValueError(f'There is no concrete wrapper method for msg_source: {msg_source}')

    return sending_method(msg_data, msg_type, provider_method, options)
