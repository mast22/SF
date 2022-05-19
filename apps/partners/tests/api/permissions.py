from apps.testing.base import BasePermissionsTestCase
from apps.testing.fixtures.data import get_random_int_string
from apps.testing.fixtures.role_testing_fixtures import create
from typing import Dict, Tuple, List

from apps.users.models import User, AccMan
from ...api import serializers as s
from ...models import Region


class RegionPermissionsTestCase(BasePermissionsTestCase):
    model = Region
    model_fixtures = [create]
    fields_to_check = []
    serializer = s.RegionSerializer
    users = {}
    regions = {}

    @classmethod
    def get_default_fields(cls, current_user):
        return {}

    @classmethod
    def setup_view_data(cls) -> Tuple[Dict[User, List], Dict]:
        allowed = {
            cls.users['admin']: [cls.regions['region_1'], cls.regions['region_2']],
            cls.users['acc_man_1']: [cls.regions['region_1']],
            cls.users['ter_man_1']: [cls.regions['region_1']],
            cls.users['ter_man_2']: [cls.regions['region_1']],
            cls.users['ter_man_3']: [cls.regions['region_2']],
            cls.users['agent_1']: [cls.regions['region_1']],
            cls.users['agent_2']: [cls.regions['region_1']],
            cls.users['agent_3']: [cls.regions['region_2']],
            cls.users['agent_4']: [cls.regions['region_2']],
        }
        forbidden = {
            cls.users['admin']: [],
            cls.users['acc_man_1']: [cls.regions['region_2']],
            cls.users['ter_man_1']: [cls.regions['region_2']],
            cls.users['ter_man_2']: [cls.regions['region_2']],
            cls.users['ter_man_3']: [cls.regions['region_1']],
            cls.users['agent_1']: [cls.regions['region_2']],
            cls.users['agent_2']: [cls.regions['region_2']],
            cls.users['agent_3']: [cls.regions['region_1']],
            cls.users['agent_4']: [cls.regions['region_1']],
        }

        return allowed, forbidden

    @classmethod
    def setup_create_data(cls):
        payload = Region(name=get_random_int_string(10), acc_man=cls.users['acc_man_1'])
        allowed = {
            cls.users['admin']: [payload],
            cls.users['acc_man_1']: [payload],
        }
        forbidden = {
            cls.users['ter_man_1']: [payload],
            cls.users['agent_1']: [payload],
        }

        return allowed, forbidden

    @classmethod
    def setup_delete_data(cls):
        allowed = {}
        forbidden = {}

        return allowed, forbidden
