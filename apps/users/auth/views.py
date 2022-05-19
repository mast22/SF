from typing import Mapping, Tuple, Union
from django.db.models import QuerySet
from django.conf import settings
from django.contrib.auth import login as django_login, logout as django_logout
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.utils import timezone as tz
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
# from rest_framework.metadata import SimpleMetadata
from rest_framework import exceptions as rest_exc
from drf_yasg.utils import swagger_auto_schema
from netaddr import IPAddress

# from apps.common import utils as u
from apps.msgs.shortcuts import send_auth_code
from apps.msgs.const import MessageType
from . import serializers as s
from .authentication import token_logout
from ..models import User, Token, TempToken, AllowedIP
from .. import const as c


sensitive_post_parameters_m = method_decorator(sensitive_post_parameters('password'))
auth_settings = getattr(settings, 'AUTH_SETTINGS', {})





class InvalidToken(rest_exc.AuthenticationFailed):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = __('Token is invalid or expired')
    default_code = 'token_not_valid'



class BaseAuthorizationView(GenericAPIView):
    """Базовый класс для процессов авторизации, регистрации и сброса пароля."""
    # Все эндпоинты доступны незарегестрированному пользователю, т.е. любому пользователю.
    permission_classes = (AllowAny,)
    # renderer_classes = [JSONRenderer]
    # metadata_class = SimpleMetadata
    serializer_class = None

    def get_queryset(self):
        # GenericApiViewset don't want to work without get_queryset!
        return QuerySet().none()

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(BaseAuthorizationView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token, is_temp_token = self.process_request(serializer, request)
        response, resp_status = self.get_success_response(user, token, is_temp_token)
        if resp_status is None:
            resp_status = status.HTTP_200_OK
        return Response(response, status=resp_status)

    def process_request(self, serializer, request) -> Tuple[User, Union[Token, Mapping], bool]:
        raise NotImplementedError('This method needs to be implemented')

    def get_success_response(self, user: User, token: Token, is_temp_token: bool=None) -> Mapping:
        raise NotImplementedError('This method needs to be implemented')

    @staticmethod
    def create_temp_token(user, type=c.TempTokenType.LOGIN_CONFIRM, **kwargs):
        assert user, 'User need to be set'
        return TempToken.objects.create(user=user, type=type, **kwargs)

    @staticmethod
    def create_token(user):
        assert user, 'User need to be set'
        refresh_token, access_token = Token.objects.create_auth_tokens(user)
        cur_moment = tz.now()
        return dict(
            now=cur_moment,
            access=str(access_token.key),
            expires=access_token.moment_end,
            refresh=str(refresh_token.key),
            refresh_expires=refresh_token.moment_end,
        )


class TokenRefreshView(GenericAPIView):
    """
    Обновление JWT-токена.
    """
    serializer_class = s.TokenRefreshSerializer
    permission_classes = (AllowAny,)
    authentication_classes = tuple()
    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            c.ACCESS_TOKEN_KEYWORD,
            self.www_authenticate_realm,
        )

    # noinspection PyTypeChecker
    @swagger_auto_schema(responses={200: s.TokenRefreshResponseSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Token.DoesNotExist as err:
            raise InvalidToken(err.args[0])
        data = self.refresh_access_token(serializer.validated_data['refresh'])
        return Response(s.TokenRefreshResponseSerializer(data).data, status=status.HTTP_200_OK)

    def refresh_access_token(self, refresh_token):
        access_token = Token.objects.renew_access_token(refresh=refresh_token)
        cur_moment = tz.now()
        return {
            'now': cur_moment,
            'expires': access_token.moment_end,
            'access': str(access_token.key),
            'user': access_token.user_id,
        }


# noinspection PyTypeChecker
@method_decorator(name='post', decorator=swagger_auto_schema(responses={
    200: s.LoginSuccessRespSerializer,
    202: s.TempTokenRespSerializaer}))
class LoginView(BaseAuthorizationView):
    """Авторизация пользователя.

    Метод доступен только неавторизованным пользователям.
    """
    serializer_class = s.LoginSerializer

    def check_user_by_role(self, user, request):
        method_to_check_user, need_temp_token = AUTHORIZATION_BY_USER_ROLE.get(user.role, (None, None))
        if method_to_check_user is None:
            raise rest_exc.PermissionDenied()
        method_to_check_user(user, request)

        if need_temp_token:
            token = self.create_temp_token(user=user)
        else:
            token = self.create_token(user)
            if auth_settings.get('use_session', False):
                django_login(request, user)
        return token, need_temp_token

    def process_request(self, serializer, request):
        user = serializer.validated_data['user']
        token, is_temp_token = self.check_user_by_role(user, request)
        return user, token, is_temp_token

    def get_success_response(self, user, token: Union[Token, TempToken, dict], is_temp_token=False):
        if is_temp_token:
            resp_serializer = s.TempTokenRespSerializaer(dict(
                detail=_('Код подтверждения успешно отправлен'),
                temp_token=token.key,
                expires=token.moment_end,
                repeat=token.can_repeat_at,
                now=tz.now(),
            ), context={'request': self.request})
            resp_http_status = status.HTTP_202_ACCEPTED
        else:
            resp_serializer = s.LoginSuccessRespSerializer(dict(
                detail=_('Вы успешно авторизовались'),
                token=token,
                user=user
            ), context={'request': self.request})
            resp_http_status = status.HTTP_200_OK
        return resp_serializer.data, resp_http_status

    @staticmethod
    def create_temp_token(user, **kwargs):
        """Генерирую временный токен с учётом всех проверок.
         TODO: Вынести этот код в отдельный метод.
         """
        assert user, 'User need to be set'

        # 1. Проверяем, сколько у юзера уже есть временных токенов:
        tokens_count = TempToken.objects.filter(
            user=user,
            moment_end__gte=tz.now(),
        ).count()
        if tokens_count >= c.TEMP_TOKEN_BAN_REPEATS_COUNT:
            raise rest_exc.Throttled()

        # 1. Проверяем, что таймаут отправки сообщения ещё не прошёл.
        tokens_repeat_count = TempToken.objects.filter(
            user=user,
            moment_end__gte=tz.now(),
            can_repeat_at__gte=tz.now(),
        ).count()
        if tokens_repeat_count:
            raise rest_exc.Throttled()

        temp_token = TempToken(user=user, type=c.TempTokenType.LOGIN_CONFIRM, **kwargs)
        if tokens_count == 0:
            # Нет таких токенов, нужно отправить дозвон с номера
            temp_token.cat_repeat_at = tz.now() + tz.timedelta(seconds=c.TEMP_TOKEN_CAN_REPEAT_DIALING_TIMEDELTA)
            send_type = MessageType.DIALING
        else:
            # Уже есть такие токены, нужно отправить SMS
            temp_token.cat_repeat_at = tz.now() + tz.timedelta(seconds=c.TEMP_TOKEN_CAN_REPEAT_SMS_TIMEDELTA)
            send_type=MessageType.SMS
        temp_token.save()

        # Отправляю код подтверждения на телефон юзеру.
        send_auth_code(temp_token, send_type=send_type)
        return temp_token


@method_decorator(name='post', decorator=swagger_auto_schema(responses={204: '= No content ='}))
class LogoutView(BaseAuthorizationView):
    serializer_class = s.EmptySerailizer

    def process_request(self, serializer, request):
        user = request.user
        if auth_settings.get('use_session', False):
            django_logout(request)
        else:
            token_logout(request)
        return user, None, None

    def get_success_response(self, user, token, is_temp_token=None):
        return None, status.HTTP_204_NO_CONTENT


# noinspection PyTypeChecker
@method_decorator(name='post', decorator=swagger_auto_schema(responses={200: s.TempTokenRespSerializaer}))
class LoginConfirmCodeView(BaseAuthorizationView):
    """
    Подтверждение проверочного кода.

    Необходимо передать временный токен и проверочный код.
    В случае успеха будет сгенерирован новый токен, который потребуется при вводе пароля.

    Возвращает ошибку в следующих случаях:
    * Не верные проверочный код или временный токен.
    * Телефон пользователя уже подтверждён (is_phone_confirmed=True),
    * Истёк срок жизни проверочного кода (возвращается в поле "expires"),
    * Пользователь заблокирован административным персоналом Oppen. (is_active=False).
    """
    serializer_class = s.LoginConfirmCodeSerializer

    def process_request(self, serializer, request):
        """
        POST: {
            "temp_token": "d9dc13e5-4f99-4355-b3f0-c58a358e6db6",
            "code": 1234
        }
        resp_BAD: (HTTP.400) { "detail": "Ошибка в проверочном коде" }
        resp_BAD: (HTTP.404) { "detail": "Передан неверный token" }
        """
        # Найти юзера по account + object_uuid:
        user = serializer.validated_data['user']

        # Меняю статус временному токену:
        # Удаляю временный токен, если найден:
        temp_token = serializer.validated_data['temp_token']
        if temp_token:
            temp_token.delete()

        # Создаю новый временный токен для ввода пароля:
        token = self.create_token(user=user)
        return user, token, False

    def get_success_response(self, user, token, is_temp_token=False):
        return s.LoginSuccessRespSerializer(dict(
            detail=_('Вы успешно авторизовались'),
            token=token,
            user=user
        ), context={'request': self.request}).data, status.HTTP_200_OK



# noinspection PyTypeChecker
@method_decorator(name='post', decorator=swagger_auto_schema(responses={200: s.TempTokenRespSerializaer}))
class PasswordResetView(BaseAuthorizationView):
    """
    Запрос на сброс пароля неавторизованным пользователем.

    В 1й раз сделает дозвон на указанный телефон пользователя,
    Во 2й и следующий разы отправит проверочный код на указанный телефон пользователя по SMS.
    Возвращает временный токен, необходимый для проверки кода и дальнейшей смены пароля.

    Возвращает ошибку в следующих случаях:
    * Пользователь не найден в базе,
    * Не истёк срок до возможности повторной отправки (возвращается в поле "repeat"),
    * Превышено максимальное количество повторных отправок.
    * Пользователь заблокирован административным персоналом Oppen. (is_active=False).

    """
    serializer_class = s.PasswordResetSerializer

    def process_request(self, serializer, request):
        """
        POST: {
            "phone": "9871234567",
        }
        resp: {
            "detail": "Код подтверждения успешно отправлен",
            "temp_token": "<temp_token>",	// Временный токен, действителен до завершения процесса смены пароля. (или до момента "expires")
            "expires": <unixtimestamp>,		// Момент времени, после которого нельзя ввести проверочный код
            "repeat": <unixtimestamp>,		// Момент времени, после которого можно будет запросить повторную отправку
        }
        """

        # Создаю новый временный токен для ввода пароля:
        user = serializer.validated_data['user']
        if not user.is_active:
            raise rest_exc.ValidationError(detail=_('Пользователь заблокирован'))
        temp_token = self.create_temp_token(user=user, type=c.TempTokenType.PASSWORD_RESET)

        # Отправляю код подтверждения юзеру на тф.
        send_auth_code(temp_token=temp_token)
        return user, temp_token, True

    def get_success_response(self, user, temp_token, is_temp_token=True):
        return s.TempTokenRespSerializaer(dict(
            detail=_('Код подтверждения успешно отправлен'),
            temp_token=temp_token.key,
            expires=temp_token.expires_at,
            repeat=temp_token.can_repeat_at,
            now=tz.now(),
        ), context={'request': self.request}).data, status.HTTP_202_ACCEPTED



# noinspection PyTypeChecker
@method_decorator(name='post', decorator=swagger_auto_schema(responses={200: s.TempTokenRespSerializaer}))
class PasswordResetConfirmCodeView(BaseAuthorizationView):
    """Проверка корректности проверочного кода при смене пароля.

    Проверяет корректность проверочного кода.
    Возвращает 200 ответ, если проверочный код верен, 400, если не верен.
    """
    serializer_class = s.PasswordResetConfirmCodeSerializer

    def process_request(self, serializer, request):
        """
        POST: {
            "temp_token": "<temp_token>,
            "code": "9871234567"
        }
        resp: {
            "detail": "Код подтверждения корректен",
        }
        """
        user = serializer.validated_data['user']

        # Меняю статус временному токену:
        # Удаляю временный токен, если найден:
        temp_token = serializer.validated_data['temp_token']
        if temp_token:
            temp_token.delete()

        # Создаю новый временный токен для ввода пароля:
        temp_token = self.create_temp_token(user=user, type=c.TempTokenType.PASSWORD_CONFIRM)
        return user, temp_token, True

    def get_success_response(self, user, temp_token: TempToken, is_temp_token=True):
        return s.TempTokenRespSerializaer(dict(
            detail=_('Проверочный код успешно подтверждён, введите пароль'),
            temp_token=temp_token.key,
            expires=temp_token.moment_end,
            repeat=temp_token.can_repeat_at,
            now=tz.now(),
        )).data, status.HTTP_200_OK


# noinspection PyTypeChecker
@method_decorator(name='post', decorator=swagger_auto_schema(responses={200:s.LoginSuccessRespSerializer}))
class PasswordResetSetPasswordView(BaseAuthorizationView):
    """
    Смена пароля при подтверждении проверочного кода.

    Необходимо передать временный токен, проверочный код и новый пароль.
    В случае успеха будет изменён пароль пользователя, также пользователь будет авторизован.

    Возвращает ошибку в следующих случаях:
    * Не верные проверочный код или временный токен.
    * Ошибка валидации нового пароля.
    * Пользователь не найден в базе,
    * Телефон пользователя ещё не подтверждён (is_phone_confirmed=False),
    * Истёк срок жизни проверочного кода (возвращается в поле "expires"),
    * Пользователь заблокирован административным персоналом Oppen. (is_active=False).

    """
    serializer_class = s.PasswordResetSetPasswordSerializer

    def process_request(self, serializer, request):
        user = serializer.validated_data['user']

        temp_token = serializer.validated_data['temp_token']
        if temp_token:
            temp_token.delete()

        user.set_password(serializer.validated_data['password'])
        user.password_reset_date = tz.now()
        user.save(update_fields=('password',))

        if auth_settings.get('use_session', True):
            django_login(request, user)

        token = self.create_token(user)
        return user, token, False

    def get_success_response(self, user, token, is_temp_token=False):
        return s.LoginSuccessRespSerializer(dict(
            detail=_('Пароль успешно изменен'),
            token=token,
            user=user
        ), context={'request': self.request}).data, status.HTTP_200_OK



def _check_ip(request, user):
    if auth_settings.get('ENABLE_IP_LIMITATION', True):
        ip_addr = get_client_ip(request)
        ip_is_allowed = AllowedIP.objects.filter(user=user, ip=ip_addr, is_active=True).exists()
        return ip_is_allowed
    else:
        return True


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', None)
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', None)
    return IPAddress(ip) if ip else None


def do_nothing(*args, **kwargs):
    """Авторизация только по логину и паролю."""
    return True


def auth_with_ip_check(user, request, *args, **kwargs):
    """Авторизация с проверкой IP-адреса"""
    if not _check_ip(request, user):
        raise rest_exc.PermissionDenied()
    return True


AUTHORIZATION_BY_USER_ROLE = {
    c.Roles.AGENT: (do_nothing, False),
    c.Roles.TER_MAN: (do_nothing, True),
    c.Roles.ACC_MAN: (auth_with_ip_check, False),
    c.Roles.ADMIN: (auth_with_ip_check, False),
}

