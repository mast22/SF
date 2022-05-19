from typing import Sequence, Tuple
from random import choice

from apps.banks.models import Bank, OutletBank
from apps.partners.models import Region, Partner, Outlet
from apps.misc.models.other import MesaBank
from apps.testing.fixtures.data import get_random_location, get_random_string, get_random_company_name, \
    get_random_int_string
from apps.users.models import User
from .users import create_terman


def create_region(acc_man: User, create=True) -> Region:
    region = Region(name=get_random_int_string(10), acc_man=acc_man)

    if create:
        region.save()

    return region


def create_partner(region: Region, ter_man: User, create=True) -> Partner:
    partner = Partner(
        region=region, ter_man=ter_man,
        name='М.Видео', legal_name='Михаил Видео',
        phone='+79993331313',
        email='m.video@yandex.ru',
        actual_address=get_random_location(),
        legal_address=get_random_location(),
        bank=create_mesa_bank()
    )

    for attr in ['TIN', 'PSRN', 'IEC', 'CA', 'giro', 'RCBIC']:
        setattr(partner, attr, 'test_data')

    if create:
        partner.save()

    return partner


def create_outlet(partner: Partner, create=True) -> Outlet:
    outlet = Outlet(
        name=get_random_company_name(),
        partner=partner, address=get_random_location(),
        telegram_id=None,
    )

    if create:
        outlet.save()

    return outlet


# def set_banks_priorities(ter_man: User, banks: Sequence[Bank], region: Region):
#     priorities = []
#     for bank in banks:
#         priorities.append(BankPriority(
#             ter_man=ter_man,
#             priority=choice(range(1,6)),
#             bank=bank,
#             # region=region,
#         ))
#
#     BankPriority.objects.bulk_create(priorities)


def create_base_structure(acc_man) -> Tuple[Region, Partner, Outlet]:
    region = create_region(acc_man)
    ter_man = create_terman(region)
    partner = create_partner(region, ter_man)
    outlet = create_outlet(partner)
    # set_banks_priorities(ter_man, banks, region)

    return region, partner, outlet


def create_mesa_bank(create=True):
    mb = MesaBank(
        name='ProElectricBank' + get_random_string(3)
    )

    if create:
        mb.save()

    return mb