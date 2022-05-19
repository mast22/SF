"""
Фикстуры, используемые для тестирования с возможностью конфигурации
Конфигурация необходима для обработки всех требований банков
"""
from typing import Tuple

from apps.banks.const import BankBrand
from apps.misc.accordance.parsing import save_csv_accordance, save_dict_accordance
from apps.orders.models import Order, OrderCreditProduct
from apps.partners.models import PartnerBank, OutletAgent
from apps.banks.models import CreditProduct, Bank, ExtraService, OutletBank, AgentBank, TerManBank

from .data import TEST_CREDIT_PRODUCT_CODE, TEST_OUTLET_CODE, TEST_AGENT_CODE, TEST_PARTNER_CODE
from .pieces.bank_products import create_credit_product, create_extra_service, set_agent_commissions
from .pieces.base_structure import create_base_structure
from .pieces.order import create_client_with_order, create_order_flow_objects
from .pieces.users import create_agent, create_terman, create_acc_man
from apps.users.models import TerMan, Agent


def set_up_fixture(bank_name: str) -> Tuple[OrderCreditProduct, CreditProduct, Order, Bank, Agent, TerMan]:
    """ Создаётся фикстура заказа, в состоянии перед отправкой на скоринг """
    assert bank_name in BankBrand.keys(), 'Данный банк не существует'

    acc_man = create_acc_man()
    bank: Bank = Bank.objects.create(name=bank_name)

    save_csv_accordance()
    save_dict_accordance()
    region, partner, outlet = create_base_structure(acc_man)
    ter_man = create_terman(region)
    agent = create_agent(ter_man=ter_man)
    client, order = create_client_with_order(agent, outlet)

    OutletBank.objects.create(
        bank=bank,
        outlet=outlet,
        code=TEST_OUTLET_CODE[bank_name]
    )
    PartnerBank.objects.create(
        bank=bank,
        partner=partner,
        code=TEST_PARTNER_CODE[bank_name]
    )
    OutletAgent.objects.create(
        agent=agent,
        outlet=outlet,
    )

    # ter_man_bank = TerManBank.objects.create(
    #     bank=bank,
    #     ter_man=ter_man,
    # )
    # AgentBank.objects.create(
    #     bank=bank,
    #     agent=agent,
    #     terman_bank=ter_man_bank,
    #     code=TEST_AGENT_CODE[bank_name],
    # )

    credit_product = create_credit_product(bank, code=TEST_CREDIT_PRODUCT_CODE[bank_name])
    extra_service = create_extra_service(bank)
    set_agent_commissions(agent, ter_man, bank, credit_product, extra_service)
    create_order_flow_objects(client=client, order=order, agent=agent, outlet=outlet)
    ocp: OrderCreditProduct = OrderCreditProduct.objects.create(
        credit_product=credit_product,
        order=order,
    )
    ocp.extra_services.set([extra_service])

    return ocp, credit_product, order, bank, agent, ter_man
