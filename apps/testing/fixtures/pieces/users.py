from typing import Tuple

from apps.testing.fixtures.data import get_random_last_name, get_random_first_name, get_random_phone
from apps.users.const import Roles, UserStatus
from apps.users.models import User, Admin, Agent, TerMan, AccMan
from apps.banks.models import Bank, AgentBank, TerManBank


def create_management(admin_phone=None, acc_man_phone=None) -> Tuple[Admin, AccMan]:
    admin = Admin(
        phone=(admin_phone or get_random_phone()), last_name=get_random_last_name(), region=None,
        first_name=get_random_first_name(), status=UserStatus.ACTIVE, role=Roles.ADMIN
    )
    admin.set_password('sf_password')

    acc_man = AccMan(
        phone=(acc_man_phone or get_random_phone()), last_name=get_random_last_name(), region=None,
        first_name=get_random_first_name(), status=UserStatus.ACTIVE, role=Roles.ACC_MAN
    )
    acc_man.set_password('sf_password')

    User.objects.bulk_create([admin, acc_man])
    return admin, acc_man


def create_terman(region, phone_number: str or None = None) -> TerMan:
    ter_man = TerMan(
        phone=(phone_number or get_random_phone()), last_name=get_random_last_name(), region=region, ter_man=None,
        first_name=get_random_first_name(), status=UserStatus.ACTIVE, can_edit_bank_priority=True,
    )
    ter_man.set_password('sf_password')
    ter_man.save()
    return ter_man


def create_agent(ter_man: User, phone_number: str or None = None) -> Agent:
    agent = Agent(
        phone=(phone_number or get_random_phone()), last_name=get_random_last_name(), ter_man=ter_man, region=None,
        first_name=get_random_first_name(), status=UserStatus.ACTIVE, role=Roles.AGENT
    )
    agent.set_password('sf_password')
    agent.save()

    return agent


def create_acc_man() -> AccMan:
    acc_man = AccMan.objects.create(
        phone=get_random_phone(), last_name=get_random_last_name(), region=None,
        first_name=get_random_first_name(), status=UserStatus.ACTIVE
    )
    acc_man.set_password('sf_password')
    return acc_man
