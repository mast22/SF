from django.db import models as m
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as __, gettext as _
from django.core.exceptions import ValidationError

from apps.common.models import BaseTokenModel, BaseTokenManager
from apps.msgs.const import SendStatus, MessageType
from .. import const as c
from .user import User
from .. import logger


class TokenManager(BaseTokenManager):
    def renew_access_token(self, refresh: 'Token'=None, refresh_key: str=None) -> 'Token':
        """Обновляет access-токен по заданному refresh-токену"""
        qs = self.get_queryset()
        assert refresh is not None or refresh_key is not None, 'Both refresh and refresh_key cant be None'
        if not refresh:
            refresh = qs.get(key=refresh_key, type=c.TokenType.REFRESH)
        if refresh.moment_end < tz.now():
            raise self.model.TokenIsOutdatedException(_('Срок действия refresh-токена закончился'))
        acc_deleted = qs.filter(parent=refresh, type=c.TokenType.ACCESS).delete()
        logger.debug(f'renew_access_token. deleted: {acc_deleted}, user_id: {refresh.user_id} refresh: {refresh}')
        access = qs.create(parent=refresh, type=c.TokenType.ACCESS, user_id=refresh.user_id)
        return access

    def create_auth_tokens(self, user: User):
        self.delete_for_user(user)
        qs = self.get_queryset()
        refresh = qs.create(user=user, type=c.TokenType.REFRESH)
        access = qs.create(user=user, type=c.TokenType.ACCESS, parent=refresh)
        return refresh, access


class Token(BaseTokenModel):
    """Токен авторизации"""
    user = m.ForeignKey(User, on_delete=m.CASCADE, null=True, default=None)
    parent = m.ForeignKey('self', on_delete=m.CASCADE, null=True, default=None)
    type = m.CharField(__('Тип'), choices=c.TokenType.as_choices(), default=c.TokenType.ACCESS, max_length=10)

    objects = TokenManager()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.user is None:
            raise ValidationError(f'Token without user is deprecated!')
        if not self.key:
            self.key = self.generate_key(c.ACCESS_TOKEN_LENGTH)
        if self.type == c.TokenType.ACCESS:
            self._setup_access_token()
        elif self.type == c.TokenType.REFRESH:
            self._setup_refresh_token()
        else:
            raise NotImplementedError(f'Tokens of this type are not implemented yet: {self.type}')
        return super().save(force_insert, force_update, using, update_fields)

    def _setup_access_token(self):
        cur_time = tz.now()
        if not self.moment_end:
            self.moment_end = cur_time + tz.timedelta(seconds=c.ACCESS_TOKEN_TIMEOUT)

    def _setup_refresh_token(self):
        cur_time = tz.now()
        if not self.moment_end:
            self.moment_end = cur_time + tz.timedelta(seconds=c.REFRESH_TOKEN_TIMEOUT)

    class Meta:
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'
        permissions = tuple()


class TempToken(BaseTokenModel):
    """Временный токен"""
    user = m.ForeignKey(User, on_delete=m.CASCADE, null=True)
    type = m.CharField(__('Тип'), choices=c.TempTokenType.as_choices(), default=c.TempTokenType.PASSWORD_RESET, max_length=14)
    phone = m.CharField(__('Номер телефона'), max_length=14, null=True)
    code = m.CharField(__('Проверочный код'), max_length=10, null=True)
    provider_uuid = m.CharField(__('Provider UUID'), max_length=200, default='', null=True, blank=True)
    send_type = m.CharField(_('Способ отправки'), choices=MessageType.as_choices(), default=MessageType.SMS, max_length=15)
    send_status = m.CharField(_('Status'), choices=SendStatus.as_choices(), default=SendStatus.NOT_SENT, max_length=10)

    received_at = m.DateTimeField(__('Дата получения'), null=True, blank=True)
    can_repeat_at = m.DateTimeField(__('Дата повтора'), blank=True,
                help_text=__('Момент времени, после которого возможна повторная отправка'))
    expires_at = m.DateTimeField(__('Дата истечения'), blank=True,
                help_text=__('Момент времени, после которого токен становится не действительным'))

    class Meta:
        verbose_name = __('Временный токен')
        verbose_name_plural = __('Временные токены')
        permissions = tuple()

    def __str__(self):
        keys = ('user', 'code', 'reg_status', 'send_status', 'can_repeat_at', 'expires_at',)
        return self.key + ' '.join(f'{k}={getattr(self, k, "")}' for k in keys)

    def clean(self):
        if not self.phone and not self.user_id:
            raise ValidationError(f'Необходимо задать номер телефона или id пользователя')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        cur_time = tz.now()
        if not self.key:
            self.key = self.generate_key(c.TEMP_TOKEN_LENGTH)
        if not self.expires_at:
            self.expires_at = cur_time + tz.timedelta(seconds=c.TEMP_TOKEN_EXPIRES_TIMEDELTA)
        if not self.can_repeat_at:
            self.can_repeat_at = cur_time + tz.timedelta(seconds=c.TEMP_TOKEN_CAN_REPEAT_DEFAULT_TIMEDELTA)
        if not self.moment_end:
            self.moment_end = cur_time + tz.timedelta(seconds=c.TEMP_TOKEN_MOMENT_END_TIMEDELTA)
        if not self.phone and self.user:
            self.phone = self.user.phone
        return super(TempToken, self).save(force_insert, force_update, using, update_fields)

    @classmethod
    def get_count(cls, user: User=None, phone: str=None, type=None) -> int:
        """Возвращает количество временных токенов, привязанных к заданному пользователю."""
        filters = {'moment_end__gt': tz.now()}
        if user:
            filters['user_id'] = user.id
        if phone:
            filters['phone'] = phone
        if type is not None:
            filters['type'] = type
        else:
            filters['type__in'] = c.TEMP_TOKEN_TYPES_WITH_COUNT_LIMIT
        tokens_count = cls.objects.filter(**filters).count()
        if tokens_count > c.TEMP_TOKEN_BAN_REPEATS_COUNT:
            raise cls.TokenLimitException(
                _('Превышено допустимое количество запросов на отправку проверочного кода'))
        return tokens_count

    @classmethod
    def create_with(cls, user=None, phone=None, code=None,
            type=c.TempTokenType.NEW_CLIENT,
            expires=c.TEMP_TOKEN_EXPIRES_TIMEDELTA,
            can_repeat=c.TEMP_TOKEN_CAN_REPEAT_SMS_TIMEDELTA,
            moment_end=c.TEMP_TOKEN_MOMENT_END_TIMEDELTA):
        """Создаёт временный токен с заданными настройками."""
        cur_time = tz.now()
        expires_at = cur_time + tz.timedelta(seconds=expires)
        can_repeat_at = cur_time + tz.timedelta(seconds=can_repeat)
        moment_end = cur_time + tz.timedelta(seconds=moment_end)
        return TempToken.objects.create(user=user, phone=phone, type=type, code=code,
               expires_at=expires_at, can_repeat_at=can_repeat_at, moment_end=moment_end)

    @classmethod
    def create_for_client(cls, phone):
        return cls.create_with(phone=phone, type=c.TempTokenType.NEW_CLIENT,
            expires=c.CLIENT_TEMP_TOKEN_EXPIRES_TIMEDELTA,
            can_repeat=c.CLIENT_TEMP_TOKEN_CAN_REPEAT_TIMEDELTA,
            moment_end=c.CLIENT_TEMP_TOKEN_MOMENT_END_TIMEDELTA,
        )
