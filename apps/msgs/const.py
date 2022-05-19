from django.utils.translation import gettext_lazy as __
from collections import namedtuple
from apps.common.choices import Choices


class SendStatus(Choices):
    NOT_SENT = 'no-sent', __('Не отправлено')
    SENT = 'sent', __('Отправлено')
    RECEIVED = 'received', __('Получено')
    # RECEIVED_PARTIALLY = 'received-partially', __('Частично получено')
    ERROR = 'error', __('Ошибка')


class MessageType(Choices):
    SMS = 'sms', __('SMS-сообщение')
    EMAIL = 'email', __('Email-сообщение')
    PUSH = 'push', __('Push-сообщение')
    VOICE_MESSAGE = 'voice-message', __('Аудио-сообщение')
    DIALING = 'dialing', __('Дозвон')
    TELEGRAM = 'telegram', __('Сообщение в Telegram')


class MessageSource(Choices):
    AUTH_CODE = 'auth-code', __('Отправка проверочного кода')
    NOTIFICATION = 'notification', __('Уведомление')
    MESSAGE = 'message', __('Сообщение')


MESSAGE_ALLOWED_TYPES_BY_SOURCE = {
    MessageSource.AUTH_CODE: tuple(MessageType),
    MessageSource.NOTIFICATION: (MessageType.SMS, MessageType.EMAIL, MessageType.PUSH),
    MessageSource.MESSAGE: (MessageType.SMS, MessageType.EMAIL, MessageType.PUSH),
}

# noinspection PyArgumentList
MessageStatus = namedtuple(
    'MessageStatus',
    (
        'delivered',  # (bool) Признак, что SMS доставлена получателю
        'error_code',  # (int or str or None) Код ошибки (зависит от провайдера)
        'error_description',  # (str or None) Описание ошибки или ответа(зависит от провайдера)
        'need_recheck',  # (bool) Необходимо проверить статус повторно
        'need_resend',  # (bool) Необходимо отправить сообщение повторно
    ),
    defaults=(False, None, None, False, False)
)

# noinspection PyArgumentList
MessageSendResult = namedtuple(
    'MessageSend',
    (
        'sent',  # (bool) Признак, что сообщение было отправлено
        'message_id',  # (str uuid) Уникальный ID сообщения у провайдера для дальнейших действий
        'code',  # (str) Проверочный код (при отправке дозвона или генерируемого кода)
        'error_code',  # (int or str or None) Код ошибки (зависит от провайдера)
        'error_description',  # (str or None) Описание ошибки или ответа(зависит от провайдера)
    ),
    defaults=(False, None, None, None, None)
)

# noinspection PyArgumentList
ProviderBalance = namedtuple(
    'ProviderBalance',
    (
        'money',  # float - Текущий балланс
        'error_code',  # (int or str or None) Код ошибки (зависит от провайдера)
        'error_description',  # (str or None) Описание ошибки или ответа(зависит от провайдера)
    ),
    defaults=(0.0, None, None)
)


DEFAULT_TASK_PARAMETERS = dict(
    max_retries=10,
    min_backoff=10_000,
    max_backoff=60_000,
    time_limit=10_000,
    max_age=600_000,
)

DEFAULT_MUTEX_PARAMETERS = dict(
    limit=100,
    bucket=1_000
)
DEFAULT_REQUEST_TIMEOUT = 10  # Секунд, таймаут запроса.

DEFAULT_CODE_LENGTH = 4


NOTIFICATIONS = {
    # Агент, Поступление новой заявки
    'new_order': {'id': 1, 'text': 'Новая заявка в системе', 'title': None,},

    # Агент. Поступление ответа банка по заявке
    'scoring_finished': {'id': 2, 'text': 'Решение банка по заявке', 'title': None},

    # Аккаунт м-р. Добавление новой Торговой точки в Регионе относящемся к Аккаунт менеджеру
    'outlet_created': {'id': 3, 'text': 'Новая Торговая Точка', 'title': None},

    # Аккаунт м-р. Добавление нового Партнера в Регионе относящемся к Аккаунт менеджеру
    'partner_created': {'id': 4, 'text': 'Новый Партнер', 'title': None},

    # Администратор. Добавление нового Территориального менеджера в систему
    'ter_man_created': {'id': 5, 'text': 'Новый Территориальный менеджер', 'title': None},

    # Аккаунт м-р. Блокировка Торговой точки
    'outlet_blocked': {'id': 6, 'text': 'Торговая точка "{name}" заблокирована', 'title': None},

    # Аккаунт м-р. Удаление Торговой точки
    'outlet_removed': {'id': 7, 'text': 'Торговая точка "name" удалена', 'title': None},

    # Администратор. Удаление Территориального менеджера
    'ter_man_removed': {'id': 8, 'text': 'Территориальный менеджер "{full_name}" удален', 'title': None},

    # Администратор. Блокировка Территориального менеджера
    'ter_man_blocked': {'id': 9, 'text': 'Территориальный менеджер "{full_name}" заблокирован', 'title': None},

    # Территориальный менеджер. Изменение в настройках комиссии Территориального менеджера
    'ter_man_comission_changed': {'id': 10, 'text': 'Ваша комиссия изменена', 'title': None},
}
