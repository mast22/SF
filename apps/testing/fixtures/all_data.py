from .pieces.bank_products import create_bank_structure, set_agent_commissions, set_outlet_banks, set_partner_banks, \
    set_outlet_agents
from .pieces.base_structure import create_base_structure
from .pieces.order import create_order_by_flow, create_client_with_order
from .pieces.users import create_agent, create_terman, create_management
from .pieces.contracts import create_deliveries
from .data import (get_random_ip, TEST_CREDIT_PRODUCT_CODE, TEST_PARTNER_CODE,
    TEST_OUTLET_CODE, TEST_AGENT_CODE, BankBrand)
from apps.users.models import AllowedIP
from typing import List

from ...misc.accordance.parsing import save_csv_accordance, save_dict_accordance

agent_phone = '+79993331313'
ter_man_phone = '+79199551650'
admin_phone = '+79709543902'
acc_man_phone = '+79088639817'


def create_fixtures(levels: List[str] or None = None):
    if levels is None:
        levels = []
    otp_with_offers, alfa_with_offers, pochta_with_offers, mts_with_offers = \
        create_bank_structure(TEST_CREDIT_PRODUCT_CODE)
    admin, acc_man = create_management(admin_phone, acc_man_phone)
    region, partner, outlet = create_base_structure(acc_man)
    save_csv_accordance()
    save_dict_accordance()
    ter_man = None
    if 'banks' in levels:
        ter_man = create_terman(region, phone_number=ter_man_phone)
        agent = create_agent(ter_man=ter_man, phone_number=agent_phone)

        # Настраиваем кредитные продукты под ОТП
        set_agent_commissions(agent, ter_man, otp_with_offers.bank, otp_with_offers.credit_product,
                              otp_with_offers.extra_service, agent_code=TEST_AGENT_CODE[BankBrand.OTP])
        set_partner_banks(partner, [otp_with_offers.bank], TEST_PARTNER_CODE)
        set_outlet_banks(outlet, [otp_with_offers.bank], TEST_OUTLET_CODE)
        set_outlet_agents(outlet, agent)

        # Настраиваем кредитные продукты под Альфу
        set_agent_commissions(agent, ter_man, alfa_with_offers.bank, alfa_with_offers.credit_product,
                              alfa_with_offers.extra_service, agent_code=TEST_AGENT_CODE[BankBrand.ALFA])
        set_partner_banks(partner, [alfa_with_offers.bank], TEST_PARTNER_CODE)
        set_outlet_banks(outlet, [alfa_with_offers.bank], TEST_OUTLET_CODE)

        # Настраиваем кредитные продукты под Почта-Банк
        set_agent_commissions(agent, ter_man, pochta_with_offers.bank, pochta_with_offers.credit_product,
                              pochta_with_offers.extra_service, agent_code=TEST_AGENT_CODE[BankBrand.POCHTA])
        set_partner_banks(partner, [pochta_with_offers.bank], TEST_PARTNER_CODE)
        set_outlet_banks(outlet, [pochta_with_offers.bank], TEST_OUTLET_CODE)

        # Настраиваем кредитные продукты под МТС-банк
        set_agent_commissions(agent, ter_man, mts_with_offers.bank, mts_with_offers.credit_product,
            mts_with_offers.extra_service, agent_code=TEST_AGENT_CODE[BankBrand.MTS])
        set_partner_banks(partner, [mts_with_offers.bank], TEST_PARTNER_CODE)
        set_outlet_banks(outlet, [mts_with_offers.bank], TEST_OUTLET_CODE)

        if 'blank_order' in levels:
            # Находимся после 1 этапа - заполнения номера, когда
            # Клиент и пустой заказ были созданы
            create_client_with_order(agent, outlet)
        if 'full_order' in levels:
            create_order_by_flow(agent, outlet, all_credit_products=(
                (otp_with_offers.credit_product, otp_with_offers.extra_service),
                (pochta_with_offers.credit_product, pochta_with_offers.extra_service),
                (mts_with_offers.credit_product, mts_with_offers.extra_service),
                (alfa_with_offers.credit_product, alfa_with_offers.extra_service),
            ), with_history=True)

    if 'extra' in levels:
        extra_orders = []
        for _ in range(25):
            admin, acc_man = create_management()
            region, partner, outlet = create_base_structure(acc_man)
            ter_man = create_terman(region)
            agent = create_agent(ter_man=ter_man)
            set_agent_commissions(agent, ter_man, otp_with_offers.bank, otp_with_offers.credit_product,
                                  otp_with_offers.extra_service, agent_code=TEST_AGENT_CODE[BankBrand.OTP])
            set_outlet_banks(outlet, [otp_with_offers.bank], TEST_OUTLET_CODE)
            extra_orders.append(
                create_order_by_flow(agent, outlet, all_credit_products=(
                    (otp_with_offers.credit_product, otp_with_offers.extra_service),
                ), with_history=True))

            set_agent_commissions(agent, ter_man, alfa_with_offers.bank, alfa_with_offers.credit_product,
                                  alfa_with_offers.extra_service, agent_code=TEST_AGENT_CODE[BankBrand.ALFA])
            set_outlet_banks(outlet, [alfa_with_offers.bank], TEST_OUTLET_CODE)
            extra_orders.append(
                create_order_by_flow(agent, outlet, all_credit_products=[
                    (alfa_with_offers.credit_product, alfa_with_offers.extra_service)
                ], with_history=True))

        create_deliveries(extra_orders)

    if 'banks' in levels:
        ips = []
        for _ in range(10):
            ips.append(AllowedIP(ip=get_random_ip(), user=create_agent(ter_man=ter_man)))

        AllowedIP.objects.bulk_create(ips)


def create_users_fixtures():
    admin, acc_man = create_management()
    region, partner, outlet = create_base_structure(acc_man)
    ter_man = create_terman(region)
    agent = create_agent(ter_man=ter_man)
    return ter_man, agent
