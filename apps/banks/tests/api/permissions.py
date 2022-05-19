from apps.testing.base import BasePermissionsTestCase
from apps.testing.fixtures.role_testing_fixtures import create
from apps.banks.models import Bank
from typing import Dict, Tuple, List
from django.db.models import Q, Model

from apps.users.models import User
from ...api import serializers as s
from ...const import BankBrand


class BanksPermissionsTestCase(BasePermissionsTestCase):
    model = Bank
    model_fixtures = [create]
    fields_to_check = []
    serializer = s.BankSerializer
    users = {}
    banks = {}

    @classmethod
    def get_default_fields(cls, current_user):
        return {}

    @classmethod
    def setup_view_data(cls) -> Tuple[Dict[User, List], Dict]:
        allowed = {
            cls.users['admin']: [cls.banks['bank_1'], cls.banks['bank_2']],
            cls.users['acc_man_1']: [cls.banks['bank_1'], cls.banks['bank_2']],
            cls.users['ter_man_1']: [cls.banks['bank_1'], cls.banks['bank_2']],
            cls.users['agent_1']: [cls.banks['bank_1'], cls.banks['bank_2']],
        }
        forbidden = {
            cls.users['admin']: [],
            cls.users['acc_man_1']: [],
            cls.users['ter_man_1']: [],
            cls.users['agent_1']: [],
        }

        return allowed, forbidden

    """
    Создание, изменение банков возможно исключительно через разработчика
    Удаление банков запрещено любым способом
    """

