from rest_framework.test import APITestCase
from apps.users import const as c
from apps.users.models import TempToken
from apps.testing.models import DummyMessage
from apps.testing.fixtures.all_data import create_users_fixtures
from ..shortcuts import send_auth_code


class AuthCodeTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        ter_man, agent = create_users_fixtures()
        ter_man.phone = '+79172225173'
        ter_man.save()
        cls.user = ter_man
        cls.tmp_token = TempToken.objects.create(user=cls.user, type=c.TempTokenType.LOGIN_CONFIRM)

    def test_send_auth_code(self):
        send_auth_code(self.tmp_token, options={'use_redis': False})
        self.tmp_token.refresh_from_db()
        self.assertIsNotNone(self.tmp_token.code, 'Auth code need to be set!')
        msg = DummyMessage.objects.filter(receiver=self.user.phone).first()
        self.assertTrue(self.tmp_token.code in msg.message, f'Auth code need to be sent to DummyMessage! Got: {msg}')

