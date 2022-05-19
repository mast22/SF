from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext as _ , ugettext_lazy as __
# from django.utils import timezone as tz
from rest_framework import serializers as s, exceptions as rest_exc
from phonenumber_field.serializerfields import PhoneNumberField

from ..models import User, Token, TempToken
from .. import const as c


class ValidateUserMixin:
    def _authenticate(self, **kwargs):
        return authenticate(self.context['request'], **kwargs)

    def _validate_phone_password(self, phone, password):
        if phone and password:
            user = self._authenticate(phone=phone, password=password)
        else:
            raise rest_exc.ValidationError(_('Необходимо ввести номер телефона и пароль'))
        user = self._validate_user_object(user)
        return user

    def _validate_user_object(self, user):
        if not user:
            raise rest_exc.PermissionDenied(_('Невозможно авторизоваться с указанными данными'))
        return user




class TokenRefreshSerializer(s.Serializer):
    refresh = s.CharField()

    def validate(self, attrs):
        refresh = Token.objects.get(key=attrs['refresh'], type=c.TokenType.REFRESH)
        attrs['refresh'] = refresh
        return attrs


class TokenRefreshResponseSerializer(s.Serializer):
    access = s.CharField(help_text=__('Access токен'))
    user = s.IntegerField(help_text=__('Пользователь'))
    expires = s.DateTimeField(help_text=__('Момент окончания действия токена'))
    now = s.DateTimeField(help_text=__('Текущее время сервера'))


class LoginSerializer(ValidateUserMixin, s.Serializer):
    phone = PhoneNumberField(required=True)
    password = s.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        attrs['user'] = self._validate_phone_password(attrs.get('phone', None), attrs.get('password', None))
        return attrs


class LoginSendCodeSerializer(s.Serializer):
    """Получение проверочного кода"""
    phone = PhoneNumberField(required=True)

    def validate(self, attrs):
        # 1. Вытащить юзера по номеру телефона
        # Проверить, что юзеру требуется подтверждение тф номера
        try:
            user = User.objects.get(phone=attrs['phone'])
        except User.DoesNotExist:
            raise rest_exc.ValidationError(code='phone_does_not_exists', detail=__('Телефон не существует'))
        if user.is_phone_confirmed:
            raise rest_exc.ValidationError()

        # 2. Проверить, нет ли на данного юзера уже записей в temp_token с repeat_at больше текущего времени
        temp_tokens_count = TempToken.get_count(user)
        if temp_tokens_count:
            raise rest_exc.Throttled(code='too_often', detail='Слишком часто слать низя, охлади тыл, подумай. 24 часа отбой.')

        attrs['user'] = user
        return attrs


class LoginConfirmCodeSerializer(s.Serializer):
    temp_token = s.CharField(required=True, min_length=64, max_length=128)
    code = s.CharField(required=True)

    def validate(self, attrs):
        # 1. Вытаскиваю temp_token:
        try:
            temp_token = TempToken.objects.get_token(attrs['temp_token'])
        except (Token.DoesNotExist, Token.TokenIsOutdatedException):
            raise rest_exc.ValidationError(code='wrong_temp_token', detail='Не верный временный token! Харам!')
        # Проверяю code:
        if temp_token.code != attrs['code']:
            raise rest_exc.ValidationError(code='wrong_code', detail='Проверочный код не верный, принимаем только кошерные коды.')

        attrs['temp_token'] = temp_token
        attrs['user'] = temp_token.user

        return attrs


class PasswordResetSerializer(s.Serializer):
    phone = PhoneNumberField(required=True)

    def validate(self, attrs):
        # 1. Вытащить юзера по номеру телефона
        # Проверить, что юзеру требуется подтверждение тф номера
        try:
            user = User.objects.get(phone=attrs['phone'])
        except User.DoesNotExist:
            raise rest_exc.ValidationError(code='phone_not_found', detail='Телефон твой - полное Г, давай по-новой.')

        # 2. Проверить, нет ли на данного юзера уже записей в temp_token,
        # с repeat_at больше текущего времени
        try:
            TempToken.get_count(user=user)
        except TempToken.TokenLimitException:
            msg = _('Слишком частая отправка')
            raise rest_exc.Throttled(code='too_often', detail='Сервер не резиновый, давай помедленнее. А лучше - завтра.')

        attrs['user'] = user
        return attrs


class PasswordResetConfirmCodeSerializer(s.Serializer):
    temp_token = s.CharField(required=True, min_length=64, max_length=128)
    code = s.CharField(required=True)

    def validate(self, attrs):
        # 1. Вытаскиваю temp_token:
        try:
            temp_token = TempToken.objects.get_token(attrs['temp_token'], c.TempTokenType.PASSWORD_RESET)
        except (Token.DoesNotExist, Token.TokenIsOutdatedException):
            raise rest_exc.ValidationError(code='wrong_temp_token', detail='Не верный временный token! Харам!')
        # Проверяю code:
        if temp_token.code != attrs['code']:
            raise rest_exc.ValidationError(code='wrong_code', detail='Проверочный код не верный, принимаем только кошерные коды.')

        attrs['temp_token'] = temp_token
        attrs['user'] = temp_token.user
        return attrs


class PasswordResetSetPasswordSerializer(s.Serializer):
    temp_token = s.CharField(required=True, min_length=64, max_length=128)
    password = s.CharField(validators=[validate_password], write_only=True, required=True,
                           style={'input_type': 'password'})

    def validate(self, attrs):
        # 1. Вытаскиваю temp_token:
        try:
            temp_token = TempToken.objects.get_token(attrs['temp_token'], c.TempTokenType.PASSWORD_CONFIRM)
        except (TempToken.DoesNotExist, TempToken.TokenIsOutdatedException):
            raise rest_exc.ValidationError(code='wrong_temp_token', detail='Не верный временный token! Харам!')

        attrs['temp_token'] = temp_token
        attrs['user'] = temp_token.user
        return attrs




# Response serializers:
from apps.users.api.serializers import UserListSerializer


class TokenResponseSerializer(s.Serializer):
    access = s.CharField()
    expires = s.DateTimeField()
    refresh = s.CharField()
    refresh_expires = s.DateTimeField()
    now = s.DateTimeField(help_text='Текущее время сервера')


class LoginSuccessRespSerializer(s.Serializer):
    detail = s.CharField()
    token = TokenResponseSerializer(read_only=True)
    user = UserListSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].context.update(self.context)


class TempTokenRespSerializaer(s.Serializer):
    detail = s.CharField()
    temp_token = s.CharField()
    expires = s.DateTimeField()
    repeat = s.DateTimeField()
    now = s.DateTimeField(help_text='Текущее время сервера')


# class LoginSendCodeRespSerializer(s.Serializer):
#     detail = s.CharField()
#     temp_token = s.CharField()
#     expires = s.DateTimeField()
#     repeat = s.DateTimeField()
#     now = s.DateTimeField(help_text='Текущее время сервера')
#
#
# class LoginConfirmCodeRespSerializer(s.Serializer):
#     detail=s.CharField()
#     temp_token = s.CharField(required=True, min_length=64, max_length=128)
#     expires=s.DateTimeField()
#     repeat = s.DateTimeField()
#     now=tz.now()
#
#
# class PasswordResetConfirmCodeRespSerializer(s.Serializer):
#     detail = s.CharField()
#     temp_token = s.CharField()
#     expires = s.DateTimeField()
#     repeat = s.DateTimeField()
#     now = s.DateTimeField(help_text='Текущее время сервера')
#
#
# class PasswordResetRespSerializer(s.Serializer):
#     detail = s.CharField()
#     temp_token = s.CharField()
#     expires = s.DateTimeField()
#     repeat = s.DateTimeField()
#     now = s.DateTimeField(help_text='Текущее время сервера')


class EmptySerailizer(s.Serializer):
    pass





