import datetime
import time
from django.utils.translation import gettext as _, gettext_lazy as __
from django.test import override_settings
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.test import APITestCase

from apps.testing.models import DummyMessage
from apps.partners.models import Region
from ...models import User, Token, TempToken, AllowedIP
from ... import const as c


def assert_success_login_response(user, test_case, resp,
            detail_msg=__('Вы успешно авторизовались'),
            resp_status=status.HTTP_200_OK):
    test_case.assertEqual(resp.status_code, resp_status, f'User: {user} Resp: {resp.json()}')
    data = resp.json()
    test_case.assertIn('detail', data, f'User: {user} Resp: {data}')
    test_case.assertEqual(data['detail'], detail_msg, f'User: {user} Resp: {data}')
    test_case.assertIn('user', data, f'User: {user} Resp: {data}')
    test_case.assertEqual(data['user']['id'], user.id, f'User: {user} Resp: {data}')
    test_case.assertIn('token', data, f'User: {user} Resp: {data}')
    test_case.assertIn('access', data['token'], f'User: {user} Resp: {data}')
    test_case.assertIn('refresh', data['token'], f'User: {user} Resp: {data}')
    return data


def assert_temp_token_response(user, test_case, resp,
        detail_msg=_('Код подтверждения успешно отправлен'),
        resp_status=status.HTTP_202_ACCEPTED):
    test_case.assertEqual(resp.status_code, resp_status, f'Resp: {resp.json()}')
    data = resp.json()
    test_case.assertIn('detail', data, f'User: {user} Resp: {resp.json()}')
    test_case.assertEqual(data['detail'], detail_msg, f'User: {user} Resp: {resp.json()}')

    temp_token = TempToken.objects.filter(user=user).first()

    test_case.assertIn('temp_token', data, f'User: {user} Resp: {resp.json()}')
    test_case.assertEqual(data['temp_token'], temp_token.key, f'User: {user} Resp: {resp.json()}')

    test_case.assertIn('expires', data, f'User: {user} Resp: {resp.json()}')
    test_case.assertIn('repeat', data, f'User: {user} Resp: {resp.json()}')
    return temp_token


def assert_code_in_dummy_msg(user, test_case: APITestCase, temp_token: TempToken):
    time.sleep(0.1)
    dm = DummyMessage.objects.filter(receiver=user.phone).last()
    test_case.assertIsNotNone(dm, f'User: {user}. There is no DummyMessage sent for this user')
    test_case.assertTrue(bool(temp_token.code), f'User: {user}. TempToken.code is empty: {temp_token}')
    test_case.assertIn(temp_token.code, dm.message, f'User: {user}. Wrong message: {dm}')
    return dm



class RefreshTokenViewTest(APITestCase):
    url = '/api/auth/refresh-token/'
    password = 'sf_password'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(phone='+79870000003', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE)
        cls.user.set_password(cls.password)
        cls.user.save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.user)
        cls.refresh_token, cls.access_token = Token.objects.create_auth_tokens(cls.user)

    def test_refresh_token_success(self):
        # Get user access/refresh tokens
        resp = self.client.post(self.url,
            {'refresh': str(self.refresh_token.key)}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, f'Resp: {resp.json()}')
        data = resp.json()
        self.assertIn('access', data)
        self.assertIn('expires', data)

    def test_refresh_token_after_login(self):
        # Get user access/refresh tokens
        login_resp = self.client.post('/api/auth/login/',
            {'phone': str(self.user.phone), 'password': self.password}, format='json')
        login_data = assert_success_login_response(self.user, self, login_resp, _('Вы успешно авторизовались'))

        resp = self.client.post(self.url, {'refresh': login_data['token']['refresh']}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, f'Resp: {resp.json()}')
        data = resp.json()
        self.assertIn('access', data)
        self.assertIn('expires', data)

    def test_refresh_token_failure(self):
        bad_refresh_token = '0' * len(self.refresh_token.key)
        resp = self.client.post(self.url, {'refresh': bad_refresh_token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, f'Resp: {resp.json()}')
        data = resp.json()
        self.assertIn('detail', data, f'Resp: {data}')
        self.assertEqual(data['detail'], 'Token matching query does not exist.', f'Resp: {data}')


@override_settings(USE_REDIS=False)
class LoginViewTest(APITestCase):
    url = '/api/auth/login/'
    password = 'sf_password'

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(phone='+79870000000', password=cls.password)
        cls.users = {
            'acc_man': User(phone='+79870000001', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE),
            'ter_man': User(phone='+79870000002', role=c.Roles.TER_MAN, status=c.UserStatus.ACTIVE),
            'agent': User(phone='+79870000003', role=c.Roles.AGENT, status=c.UserStatus.ACTIVE),
        }
        for user in cls.users.values():
            user.set_password(cls.password)
        cls.users['acc_man'].save()
        region = Region.objects.create(name='test-region', acc_man=cls.users['acc_man'], is_active=True)
        cls.users['ter_man'].region = region
        cls.users['ter_man'].save()
        cls.users['agent'].ter_man = cls.users['ter_man']
        cls.users['agent'].save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.superuser)
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.users['acc_man'])

    def test_login_admin__acc_man__agent(self):
        for user in self.superuser, self.users['acc_man'], self.users['agent']:
            resp = self.client.post(self.url,
                {'phone': str(user.phone), 'password': self.password},
                format='json')
            assert_success_login_response(user, self, resp, _('Вы успешно авторизовались'))

    def test_login_ter_man(self):
        user = self.users['ter_man']
        resp = self.client.post(self.url,
            {'phone': str(user.phone), 'password': self.password},
            format='json')
        temp_token = assert_temp_token_response(user, self, resp, _('Код подтверждения успешно отправлен'))
        assert_code_in_dummy_msg(user, self, temp_token)

    def test_already_logged_in_user(self):
        self.client.login(phone=self.superuser.phone, password='sf_password')
        resp = self.client.post(self.url,
            {'phone': str(self.superuser.phone), 'password': 'sf_password'},
            format='json')
        assert_success_login_response(self.superuser, self, resp, _('Вы успешно авторизовались'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, f'Resp: {resp.json()}')

    def test_user_does_not_exists(self):
        resp = self.client.post(self.url, {'phone': '+79871234568', 'password': 'sf_password'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, f'Resp: {resp.json()}')

    def test_user_is_blocked(self):
        self.superuser.status = c.UserStatus.BLOCKED
        self.superuser.save()
        resp = self.client.post(self.url, {'phone': str(self.superuser.phone), 'password': 'sf_password'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, f'Resp: {resp.json()}')

    def test_old_tokens_are_deleted_on_login(self):
        pass

    def test_admin_login_wrong_ip(self):
        AllowedIP.objects.all().delete()
        resp = self.client.post(self.url, {'phone': str(self.superuser.phone), 'password': 'sf_password'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, f'Resp: {resp.json()}')


class TokenAuthenticationTestCase(APITestCase):
    url = '/api/orders/'
    password = 'sf_password'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(phone='+79870000003', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE)
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.refresh_token, cls.access_token = Token.objects.create_auth_tokens(cls.user)

    def test_user_can_access_resource_with_token(self):
        auth_header = f'Token {str(self.access_token.key)}'
        resp = self.client.get(self.url, HTTP_AUTHORIZATION=auth_header, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_cannot_access_resource_with_outdated_token(self):
        self.access_token.moment_end = tz.now() # Нельзя предоставить доступ, если действие токена истекает сейчас
        self.access_token.save()
        auth_header = f'Token {str(self.access_token.key)}'
        resp = self.client.get(self.url, HTTP_AUTHORIZATION=auth_header, format='json')
        self.assertNotEqual(resp.status_code, status.HTTP_200_OK)


class LogoutViewTest(APITestCase):
    url = '/api/auth/logout/'
    password = 'sf_password'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(phone='+79870000003', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE)
        cls.user.set_password(cls.password)
        cls.user.save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.user)

    def test_logout_success(self):
        self.refresh_token, self.access_token = Token.objects.create_auth_tokens(self.user)
        auth_header = f'Token {str(self.access_token.key)}'
        resp = self.client.post(self.url, None, format='json', HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT, f'Resp: {resp.content}')

    def test_logout_failure(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, f'Resp: {resp.content}')

    def test_tokens_are_removed_on_logout(self):
        pass


class ConfirmRegistrationCodeViewTestCase(APITestCase):
    url = '/api/auth/login/confirm-code/'

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('+79870000001', '12345!54321')
        region = Region.objects.create(acc_man=cls.admin, name='Регион', is_active=True)
        cls.user = User(phone='+79870000003', role=c.Roles.TER_MAN, region=region, status=c.UserStatus.ACTIVE)
        cls.user.set_unusable_password()
        cls.user.save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.admin)
        cls.temp_token = TempToken.objects.create(
            user=cls.user,
            code='1234',
        )

    def test_confirm_code_success(self):
        resp = self.client.post(self.url, {
            'temp_token': str(self.temp_token.key),
            'code': str(self.temp_token.code),
        }, format='json')
        assert_success_login_response(self.user, self, resp)



class PasswordResetViewTest(APITestCase):
    url = '/api/auth/password-reset/'
    password = 'sf_password'
    new_password = '54321@12345'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(phone='+79870000003', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE)
        cls.user.set_password(cls.password)
        cls.user.save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.user)

    def test_reset_password_success(self):
        resp = self.client.post(self.url, {
            'phone': str(self.user.phone)
        }, format='json')
        assert_temp_token_response(self.user, self, resp)

        # msg = DummyMessage.objects.first()
        # self.assertIn(temp_token.code, msg.message, f'Resp: {data}')
        # self.assertEqual(msg.receiver, self.user.phone, f'Resp: {data}')

    def test_reset_password_wrong_phone(self):
        resp = self.client.post(self.url, {
            'phone': '+79871234500'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, f'Resp: {resp.json()}')
        data = resp.json()
        # self.assertEqual()


class PasswordResetConfirmCodeViewTest(APITestCase):
    url = '/api/auth/password-reset/confirm-code/'
    password = 'sf_password'
    code = '1234'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(phone='+79870000003', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE)
        cls.user.set_password(cls.password)
        cls.user.save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.user)
        cls.temp_token = TempToken.objects.create(
            user=cls.user,
            code=cls.code,
            type=c.TempTokenType.PASSWORD_RESET,
        )

    def test_confirm_code_success(self):
        resp = self.client.post(self.url, {
            'code': self.temp_token.code,
            'temp_token': self.temp_token.key,
        }, format='json')
        assert_temp_token_response(self.user, self, resp,
                _('Проверочный код успешно подтверждён, введите пароль'), status.HTTP_200_OK)

    def test_reset_password_wrong_code(self):
        resp = self.client.post(self.url, {
            'code': '4321',
            'temp_token': self.temp_token.key,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, f'Resp: {resp.json()}')

    def test_reset_password_wrong_token(self):
        bad_token = '0' * len(self.temp_token.key)
        resp = self.client.post(self.url, {
            'code': self.temp_token.code,
            'temp_token': bad_token,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, f'Resp: {resp.json()}')


class PasswordResetSetPasswordViewTest(APITestCase):
    url = '/api/auth/password-reset/set-password/'
    password = 'sf_password'
    new_password = 'Prodolb@li Vse PolimerbI'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(phone='+79870000003', role=c.Roles.ACC_MAN, status=c.UserStatus.ACTIVE)
        cls.user.set_password(cls.password)
        cls.user.save()
        AllowedIP.objects.create(ip='127.0.0.1', user=cls.user)
        cls.temp_token = TempToken.objects.create(
            user=cls.user,
            type=c.TempTokenType.PASSWORD_CONFIRM,
        )

    def test_reset_password_success(self):
        resp = self.client.post(self.url, {
            'password': self.new_password,
            'temp_token': self.temp_token.key,
        }, format='json')
        assert_success_login_response(self.user, self, resp, _('Пароль успешно изменен'))

    def test_user_can_login_after_password_reset(self):
        resp = self.client.post(self.url, {
            'password': self.new_password,
            'temp_token': self.temp_token.key,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, f'Resp: {resp.json()}')

        self.client.logout()
        resp = self.client.post('/api/auth/login/', {
            'phone': str(self.user.phone), 'password': self.new_password,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, f'Resp: {resp.json()}')

    def test_reset_password_wrong_token(self):
        bad_token = '0' * len(self.temp_token.key)
        resp = self.client.post(self.url, {
            'password': self.new_password,
            'temp_token': bad_token,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, f'Resp: {resp.json()}')


class FullAuthorizationProcessTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_ter_man__login__logout__login__logout(self):
        pass

    def test_agent__reset_password__login__logout(self):
        pass
