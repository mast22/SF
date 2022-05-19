from decimal import Decimal

from apps.banks.const import BankBrand
from apps.banks.models import Bank, AgentBank, AgentCreditProduct, OutletBank, TerManBank, TerManCreditProduct, \
    TerManExtraService, CreditProduct, ExtraService
from apps.orders.models import Client, ClientOrder, Order
from apps.partners.models import Region, Partner, Outlet, OutletAgent, PartnerBank
from apps.testing.fixtures.data import get_random_phone, get_random_first_name, get_random_last_name, \
    get_random_int_string, TEST_CREDIT_PRODUCT_CODE
from apps.testing.fixtures.pieces.bank_products import create_credit_product, create_extra_service
from apps.testing.fixtures.pieces.base_structure import create_region, create_partner, create_outlet
from apps.testing.fixtures.pieces.users import create_management, create_acc_man
from apps.users.const import Roles, UserStatus
from apps.users.models import User, Agent, TerMan, AccMan, Admin


def create_user(**kwargs) -> User:
    last_name = kwargs.pop('last_name', None)
    user = User(
        **kwargs,
        phone=get_random_phone(), last_name=(last_name or get_random_last_name()),
        first_name=get_random_first_name(),
        status=UserStatus.ACTIVE
    )
    user.set_password('sf_password')

    # Подставим правильный класс пользователя
    substitute_classes = {
        Roles.AGENT: Agent,
        Roles.TER_MAN: TerMan,
        Roles.ACC_MAN: AccMan,
        Roles.ADMIN: Admin
    }
    user.__class__ = substitute_classes[kwargs['role']]

    return user


def create_ter_man_credit_product(terman_bank: TerManBank, credit_product: CreditProduct) -> TerManCreditProduct:
    return TerManCreditProduct(
        terman_bank=terman_bank,
        credit_product=credit_product,
        commission_min=Decimal(0.10),
        commission_max=Decimal(50),
    )

def create():
    admin = create_user(role=Roles.ADMIN)

    bank_1 = Bank(name=BankBrand.OTP)
    bank_2 = Bank(name=BankBrand.ALFA)
    Bank.objects.bulk_create([bank_1, bank_2])

    acc_man_1 = create_user(role=Roles.ACC_MAN, last_name='acc_man_1')
    acc_man_2 = create_user(role=Roles.ACC_MAN, last_name='acc_man_2')
    User.objects.bulk_create([acc_man_1, acc_man_2, admin])

    region_1 = create_region(acc_man_1, create=False)
    region_2 = create_region(acc_man_2, create=False)
    Region.objects.bulk_create([region_1, region_2])

    ter_man_1 = create_user(role=Roles.TER_MAN, region=region_1, can_edit_bank_priority=True, last_name='ter_man_1')
    ter_man_2 = create_user(role=Roles.TER_MAN, region=region_1, can_edit_bank_priority=True, last_name='ter_man_2')
    ter_man_3 = create_user(role=Roles.TER_MAN, region=region_2, can_edit_bank_priority=True, last_name='ter_man_3')
    User.objects.bulk_create([ter_man_1, ter_man_2, ter_man_3])

    partner_1 = create_partner(region_1, ter_man_1, create=False)
    partner_2 = create_partner(region_1, ter_man_2, create=False)
    partner_3 = create_partner(region_2, ter_man_3, create=False)
    Partner.objects.bulk_create([partner_1, partner_2, partner_3])

    outlet_1_1 = create_outlet(partner=partner_1, create=False)
    outlet_1_2 = create_outlet(partner=partner_1, create=False)
    outlet_2 = create_outlet(partner=partner_2, create=False)
    outlet_3 = create_outlet(partner=partner_3, create=False)
    outlet_5 = create_outlet(partner=partner_1, create=False)
    outlet_6 = create_outlet(partner=partner_1, create=False)
    Outlet.objects.bulk_create([outlet_1_1, outlet_1_2, outlet_2, outlet_3, outlet_5, outlet_6])

    agent_1 = create_user(role=Roles.AGENT, ter_man=ter_man_1, last_name='agent_1')
    agent_2 = create_user(role=Roles.AGENT, ter_man=ter_man_2, last_name='agent_2')
    agent_3 = create_user(role=Roles.AGENT, ter_man=ter_man_3, last_name='agent_3')
    agent_4 = create_user(role=Roles.AGENT, ter_man=ter_man_3, last_name='agent_4')
    agent_5 = create_user(role=Roles.AGENT, ter_man=ter_man_1, last_name='agent_5')
    agent_6 = create_user(role=Roles.AGENT, ter_man=ter_man_1, last_name='agent_6')
    User.objects.bulk_create([agent_1, agent_2, agent_3, agent_4, agent_5, agent_6])

    outlet_1_1_agent_1 = OutletAgent(agent=agent_1, outlet=outlet_1_1)
    outlet_5_agent_5 = OutletAgent(agent=agent_5, outlet=outlet_5)
    outlet_6_agent_6 = OutletAgent(agent=agent_6, outlet=outlet_6)
    OutletAgent.objects.bulk_create([outlet_1_1_agent_1, outlet_5_agent_5, outlet_6_agent_6])

    partner_1_bank_1 = PartnerBank(bank=bank_1, partner=partner_1, code=get_random_int_string(4))
    partner_2_bank_1 = PartnerBank(bank=bank_1, partner=partner_2, code=get_random_int_string(4))
    PartnerBank.objects.bulk_create([partner_1_bank_1, partner_2_bank_1])

    ter_man_1_bank_1 = TerManBank(bank=bank_1, ter_man=ter_man_1)
    ter_man_2_bank_1 = TerManBank(bank=bank_1, ter_man=ter_man_2)
    TerManBank.objects.bulk_create([ter_man_1_bank_1, ter_man_2_bank_1])

    agent_1_bank_1 = AgentBank(bank=bank_1, agent=agent_1, terman_bank=ter_man_1_bank_1, code=get_random_int_string(4))
    agent_2_bank_1 = AgentBank(bank=bank_1, agent=agent_2, terman_bank=ter_man_1_bank_1, code=get_random_int_string(4))
    agent_5_bank_1 = AgentBank(bank=bank_1, agent=agent_5, terman_bank=ter_man_1_bank_1, code=get_random_int_string(4))
    agent_6_bank_1 = AgentBank(bank=bank_1, agent=agent_6, terman_bank=ter_man_1_bank_1, code=get_random_int_string(4))
    AgentBank.objects.bulk_create([agent_1_bank_1, agent_2_bank_1, agent_5_bank_1, agent_6_bank_1])

    # ob_1_1_1 = OutletBank.objects.create(outlet=outlet1_1, bank=bank_1)
    # ob_1_2_1 = OutletBank.objects.create(outlet=outlet1_2, bank=bank_1)
    # ob_2_1 = OutletBank.objects.create(outlet=outlet_2, bank=bank_2)
    # ob_3_1 = OutletBank.objects.create(outlet=outlet_3, bank=bank_2)
    outlet_5_bank_1 = OutletBank.objects.create(outlet=outlet_5, bank=bank_1, code=get_random_int_string(4))
    outlet_6_bank_1 = OutletBank.objects.create(outlet=outlet_6, bank=bank_1, code=get_random_int_string(4))

    credit_product_1 = create_credit_product(bank_1, code=TEST_CREDIT_PRODUCT_CODE[bank_1.name], save=False)
    credit_product_2 = create_credit_product(bank_1, code=TEST_CREDIT_PRODUCT_CODE[bank_1.name], save=False)
    credit_product_3 = create_credit_product(bank_1, code=TEST_CREDIT_PRODUCT_CODE[bank_1.name], save=False)
    credit_product_4 = create_credit_product(bank_1, code=TEST_CREDIT_PRODUCT_CODE[bank_1.name], save=False)
    credit_product_5 = create_credit_product(bank_1, code=TEST_CREDIT_PRODUCT_CODE[bank_1.name], save=False)
    credit_product_6 = create_credit_product(bank_1, code=TEST_CREDIT_PRODUCT_CODE[bank_1.name], save=False)

    CreditProduct.objects.bulk_create([
        credit_product_1, credit_product_2, credit_product_3, credit_product_4, credit_product_5, credit_product_6
    ])

    extra_service_1 = create_extra_service(bank_1, save=False)
    extra_service_2 = create_extra_service(bank_1, save=False)
    extra_service_3 = create_extra_service(bank_1, save=False)

    ExtraService.objects.bulk_create([
        extra_service_1, extra_service_2, extra_service_3
    ])
    """
    Необходимо проверить 2 ответвления на каждом из уровней
    В одном из них агент может изменить заказа, в другом нет
    Возможность создать добивается путем наличия всех промежуточных объектов (уровней),
    А отсутствие возможности - отсутствием объекта или его не активность (is_active=False)
    В фикстурах мы не предусматриваем неактивные объекты, иначе бы это усложнило тестирование
    Для credit_product_1 должно проходить всё
    Для credit_product_2 отсутствует AgentCreditProduct, его добавить нельзя в заказ
    Для credit_product_3 отсутствует TerManCreditProduct, его добавить нельзя в заказ
    Для credit_product_4 присутствует TerManCreditProduct, но у AgentCreditProduct он будет привязан к другому агенту
    Для credit_product_5 TerManCreditProduct привязан к другому ter_man`у
    Для credit_product_6 отсутствует все объекты
    """

    ter_man_1_credit_product_1 = create_ter_man_credit_product(ter_man_1_bank_1, credit_product_1)
    ter_man_1_credit_product_2 = create_ter_man_credit_product(ter_man_1_bank_1, credit_product_2)
    ter_man_1_credit_product_4 = create_ter_man_credit_product(ter_man_1_bank_1, credit_product_4)
    ter_man_2_credit_product_5 = create_ter_man_credit_product(ter_man_2_bank_1, credit_product_5)
    TerManCreditProduct.objects.bulk_create([
        ter_man_1_credit_product_1, ter_man_1_credit_product_2, ter_man_1_credit_product_4, ter_man_2_credit_product_5
    ])

    agent_5_credit_product_1 = AgentCreditProduct(
        commission=Decimal(2),
        credit_product=credit_product_1,
        agent_bank=agent_5_bank_1,
        terman_credit_product=ter_man_1_credit_product_1,
    )
    agent_6_credit_product_4 = AgentCreditProduct(
        commission=Decimal(2),
        credit_product=credit_product_4,
        agent_bank=agent_6_bank_1,
        terman_credit_product=ter_man_1_credit_product_4,
    )
    AgentCreditProduct.objects.bulk_create([agent_5_credit_product_1, agent_6_credit_product_4])

    phone_1 = get_random_phone()
    phone_2 = get_random_phone()
    phone_3 = get_random_phone()
    phone_5 = get_random_phone()
    phone_6 = get_random_phone()

    client_1 = Client(phone=phone_1)
    client_2 = Client(phone=phone_2)
    client_3 = Client(phone=phone_3)
    client_5 = Client(phone=phone_5)
    client_6 = Client(phone=phone_6)
    Client.objects.bulk_create([client_1, client_2, client_3, client_5, client_6])

    client_order_1 = ClientOrder(phone=phone_1, client=client_1)
    client_order_3 = ClientOrder(phone=phone_3, client=client_3)
    client_order_2 = ClientOrder(phone=phone_2, client=client_2)
    client_order_5 = ClientOrder(phone=phone_5, client=client_5)
    client_order_6 = ClientOrder(phone=phone_6, client=client_6)
    ClientOrder.objects.bulk_create([client_order_1, client_order_3, client_order_2, client_order_5, client_order_6])

    # Заказы для проверки добавления кредитных продуктов

    # Заказы для проверки обновления
    order_1 = Order(client_order=client_order_1, agent=agent_1, outlet=outlet_1_1)
    order_3 = Order(client_order=client_order_3, agent=agent_3, outlet=outlet_3)
    order_5 = Order(client_order=client_order_5, agent=agent_5, outlet=outlet_5)
    order_6 = Order(client_order=client_order_6, agent=agent_6, outlet=outlet_6)
    Order.objects.bulk_create([order_1, order_3, order_5, order_6])

    # TODO Проверить создание заказа если нет OutletBank

    return {
        'users': {
            'admin': admin, 'acc_man_1': acc_man_1, 'acc_man_2': acc_man_2, 'ter_man_1': ter_man_1,
            'ter_man_2': ter_man_2, 'ter_man_3': ter_man_3, 'agent_1': agent_1, 'agent_2': agent_2,
            'agent_3': agent_3, 'agent_4': agent_4, 'agent_5': agent_5, 'agent_6': agent_6
        },
        'banks': {'bank_1': bank_1, 'bank_2': bank_2},
        'regions': {'region_1': region_1, 'region_2': region_2},
        'orders': {'order_1': order_1, 'order_3': order_3, 'order_5': order_5, 'order_6': order_6},
        'outlets': {
            'outlet1_1': outlet_1_1, 'outlet1_2': outlet_1_2, 'outlet_2': outlet_2,
            'outlet_3': outlet_3, 'outlet_5': outlet_5, 'outlet_6': outlet_6
        },
        'client_orders': {'client_order_1': client_order_1,'client_order_3': client_order_3},
        'clients': {'client_1': client_1,'client_3': client_3, 'client_5': client_5, 'client_6': client_6},
        'credit_products': {
            'credit_product_1': credit_product_1, 'credit_product_2': credit_product_2,
            'credit_product_3': credit_product_3, 'credit_product_4': credit_product_4,
            'credit_product_5': credit_product_5, 'credit_product_6': credit_product_6,
        },
        'outlet_agent': {
            'outlet_5_agent_5': outlet_5_agent_5,
            'outlet_6_agent_6': outlet_6_agent_6,
        },
        'extra_service': {'extra_service_1': extra_service_1,'extra_service_2': extra_service_2},
    }
