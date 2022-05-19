from apps.common.choices import Choices
from django.utils.translation import gettext_lazy as __


class Roles(Choices):
    ADMIN = 'admin', __('Администратор')
    ACC_MAN = 'acc_man', __('Аккаунт-мереджер')
    TER_MAN = 'ter_man', __('Территориальный-менеджер')
    AGENT = 'agent', __('Агент')


# Роли, которым разрешён доступ только с определённого набора IP-адресов
ROLES_BY_IP = (Roles.ADMIN, Roles.ACC_MAN)
# Роли, для которых обязательна отправка проверочного кода
ROLES_BY_CODE = (Roles.TER_MAN,)


class TokenType(Choices):
    ACCESS = 'access', __('Токен доступа')
    REFRESH = 'refresh', __('Токен обновления')


ACCESS_TOKEN_LENGTH = 128
ACCESS_TOKEN_TIMEOUT = 10000
REFRESH_TOKEN_TIMEOUT = 1000000
ACCESS_TOKEN_KEYWORD = 'Token'


class TempTokenType(Choices):
    LOGIN_CONFIRM = 'login-confirm', __('Подтверждение при входе')
    PASSWORD_RESET = 'passwd-reset', __('Сброс пароля')
    PASSWORD_CONFIRM = 'passwd-confirm', __('Подтверждение пароля')
    NEW_CLIENT = 'new-client', __('Добавление клиента')


# Временные токены, при создании которых отправляется смс/дозвон и их кол-во необходимо ограничить:
TEMP_TOKEN_TYPES_WITH_COUNT_LIMIT = (TempTokenType.LOGIN_CONFIRM, TempTokenType.PASSWORD_RESET)
TEMP_TOKEN_LENGTH = 64
TEMP_TOKEN_EXPIRES_TIMEDELTA = 600 # В течении какого времени можно пользоваться временным токеном
TEMP_TOKEN_CAN_REPEAT_DEFAULT_TIMEDELTA = 180
TEMP_TOKEN_CAN_REPEAT_DIALING_TIMEDELTA = 60
TEMP_TOKEN_CAN_REPEAT_SMS_TIMEDELTA = 180
TEMP_TOKEN_MOMENT_END_TIMEDELTA = 60*60*24 # Банить на сутки!
TEMP_TOKEN_BAN_REPEATS_COUNT = 10


# Ограничения на временные токены при отправке смс клиенту:
CLIENT_TEMP_TOKEN_EXPIRES_TIMEDELTA = 3600
CLIENT_TEMP_TOKEN_CAN_REPEAT_TIMEDELTA = 180
CLIENT_TEMP_TOKEN_MOMENT_END_TIMEDELTA = 60*60*24


class UserStatus(Choices):
    """
    Для контроля блокировки пользователя раздёлена блокировка
    на восстановимую "blocked" и невосстановимую "removed"
    """
    ACTIVE = 'active', __('Активен')
    BLOCKED = 'blocked', __('Заблокирован')
    REMOVED = 'removed', __('Удалён')
