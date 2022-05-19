import os
import random
from typing import Sequence, Tuple
from datetime import datetime
from django.core.files import File
from django.conf import settings

from apps.banks.models import CreditProduct, ExtraService
from apps.misc.models.accordance import Accordance
from apps.orders.const import (OrderStatus, Sex, WorkerSocialStatus, RealtyType,
    Education, MaritalStatus, CreditProductStatus, ContactRelation, WorkplaceCategory )
from apps.orders.models import Order, PersonalData, CareerEducation, ExtraData, Good, OrderGood, \
    OrderCreditProduct, Client, Passport, FamilyData, Credit, ClientOrder, OrderHistory
from apps.partners.const import Country
from apps.partners.models import Outlet
from apps.testing.fixtures.data import (get_random_phone,
    get_random_first_name, get_random_last_name,
    get_random_date, get_random_int_string, get_random_location,
    get_random_company_name, get_random_date_between,
)
from apps.users.models import User


def create_client_with_order(agent: User, outlet: Outlet) -> Tuple[Client, Order]:
    phone = get_random_phone()
    client = Client.objects.create(phone=phone)
    client_order = ClientOrder.objects.create(client=client, phone=phone)
    order = Order.objects.create(client_order=client_order, agent=agent, outlet=outlet)

    return client, order


def create_order_flow_objects(client, order, agent, outlet):
    phone_category = Accordance.objects.get(general='MOBILE_PHONE')
    auto_parts = Accordance.objects.get(general='CAR_REPAIR')
    pc_and_parts = Accordance.objects.get(general='COMPUTER_COMPONENTS')
    good_appearance = Accordance.objects.get(general='SUCCESS')
    position_type_specialist = Accordance.objects.get(general='SPEC')
    org_ownership = Accordance.objects.get(general='PRIVATE')
    org_industry = Accordance.objects.get(general='AGRICULTURE')

    goods = [
        Good(brand='Iphone', model='12', category=phone_category, name='Мобильный телефон'),
        Good(brand='Samsung', model='14', category=phone_category, name='Мобильный телефон'),
        Good(brand='Toyota', model='Carda shaft', category=auto_parts, name='Карданный вал'),
        Good(brand='DELL', model='Inspirion G5', category=pc_and_parts, name='Ноутбук'),
    ]
    Good.objects.bulk_create(goods)
    birth_date = datetime(1999, 12, 13)
    passport = Passport.objects.create(
        client=client,
        order=order,
        first_name=get_random_first_name(),
        last_name=get_random_last_name(),
        birth_date=birth_date,
        number=get_random_int_string(6),
        series=get_random_int_string(4),
        receipt_date=datetime(2020, 1, 1),
        division_code=f'{get_random_int_string(3)}-{get_random_int_string(3)}',
        issued_by=f'Lorem ipsum dolor sit amet',
        sex=Sex.MALE,
    )

    picture_path = os.path.join(settings.BASE_DIR, 'apps/orders/tests/picture.jpg')
    passport.passport_main_photo.save('picture.jpg', File(open(picture_path, 'rb')))
    passport.passport_registry_photo.save('picture.jpg', File(open(picture_path, 'rb')))
    passport.previous_passport_photo.save('picture.jpg', File(open(picture_path, 'rb')))
    passport.client_photo.save('picture.jpg', File(open(picture_path, 'rb')))

    Credit.objects.create(
        client=client,
        order=order,
        initial_payment=25000,
        term=24,
    )

    PersonalData.objects.create(
        client=client,
        order=order,

        birth_place=get_random_int_string(8),
        birth_country=random.choice(Country.keys()),
        registry_location=get_random_location(),
        registry_date=get_random_date_between(birth_date, datetime.now()),
        habitation_location=get_random_location(),
        habitation_realty_type=random.choice(RealtyType.keys()),
        realty_period_months=random.randint(1, 12),

        life_insurance_code=None,
        work_loss_insurance_code=None,
        contact_first_name=get_random_first_name(),
        contact_last_name=get_random_last_name(),
        contact_phone=get_random_phone(),
        contact_relation=ContactRelation.RELATIVE,
        appearance=good_appearance
    )

    CareerEducation.objects.create(
        client=client,
        order=order,

        is_student=False,
        worker_status=WorkerSocialStatus.FULL_TIME,
        position_type=position_type_specialist,
        retiree_status=None,

        education=random.choice(Education.keys()),
        org_name=get_random_company_name(),
        org_industry=org_industry,
        position='Работник',
        months_of_exp=random.randint(1, 12),
        org_location=get_random_location(),
        job_phone=get_random_phone(),
        monthly_income=random.randint(10000, 1000000),

        workplace_category=WorkplaceCategory.FULL_TIME,
        monthly_expenses=random.randint(10000, 1000000),
        org_ownership=org_ownership,
    )

    ExtraData.objects.create(client=client, order=order)

    FamilyData.objects.create(
        client=client,
        order=order,
        marital_status=MaritalStatus.MARRIED,
        marriage_date=get_random_date(),
        partner_first_name=get_random_first_name(),
        partner_last_name=get_random_last_name(),
        partner_is_student=False,
        partner_worker_status=WorkerSocialStatus.FULL_TIME,
        partner_position_type=position_type_specialist,
        partner_retiree_status=None,
        monthly_family_income=random.randint(10000, 1000000),
        code_word='кодовое слово',
        children_count=random.randint(1, 10),
        dependents_count=random.randint(1, 10),
    )

    # outlet.code = '3632' # OTP outlet_bank!
    # outlet.save()
    #
    # agent.code = '004451320751512813' # OTP agent_bank!
    # agent.save()

    order.agent = agent
    order.outlet = outlet

    order_goods = []
    purchase_amount = 0
    for good in goods:
        price = 10000
        amount = 3
        purchase_amount += price * amount
        order_goods.append(
            OrderGood(
                good=good,
                order=order,
                price=price,
                amount=amount,
            )
        )

    order.purchase_amount = purchase_amount
    order.save()
    OrderGood.objects.bulk_create(order_goods)


def create_order_by_flow(
        agent: User,
        outlet: Outlet,
        chosen_product: OrderCreditProduct=None,
        all_credit_products: Sequence[Tuple[CreditProduct, ExtraService]]=None,
        with_history: bool=False,
) -> Order:
    client, order = create_client_with_order(agent, outlet)
    create_order_flow_objects(client=client, order=order, agent=agent, outlet=outlet)

    order.chosen_product = chosen_product
    order.save()

    order.credit_products.set(tuple(cp for cp, _ in all_credit_products))
    ocps = order.order_credit_products.order_by('id').all()
    for (credit_product, extra_service), ocp in zip(all_credit_products, ocps):
        ocp.extra_services.set([extra_service])
        if chosen_product and credit_product.id == chosen_product.id:
            order.extra_services.set([extra_service])

    if chosen_product:
        chosen_product.status = CreditProductStatus.SUCCESS
        chosen_product.save()

    order_history_objects = []
    if with_history:
        ocps = list(order.order_credit_products.all())
        for _ in range(30):
            action_keyword = [
                (OrderStatus.NEW, None, ''),
                (OrderStatus.SCORING, None, ''),
                (OrderStatus.SELECTION, CreditProductStatus.SUCCESS, 'Клиент выбрал банк'),
                (OrderStatus.SCORING, CreditProductStatus.REJECTED, 'Отказал по скорингу'),
                (OrderStatus.SCORING, CreditProductStatus.TECHNICAL_ERROR, 'Отказал в скоринге: ошибка в заполнении'),
                (OrderStatus.DOCUMENTS_CREATION, CreditProductStatus.SUCCESS, 'Скоринг прошёл!'),
                (OrderStatus.REJECTED, CreditProductStatus.REJECTED, 'Отказал в скоринге: подозрительный клиент'),
                (OrderStatus.REJECTED, CreditProductStatus.REJECTED, 'Отказал в скоринге: недостаточно денег у банка'),
                (OrderStatus.CLIENT_REFUSED, CreditProductStatus.SUCCESS, 'Клиент отказался: подозрительный банк'),
            ]
            order_status, cp_status, descr = random.choice(action_keyword)
            ocp = random.choice(ocps)
            order_history_objects.append(OrderHistory(
                order=order, order_status=order_status,
                credit_product=ocp, credit_product_status=cp_status,
                description=descr,
            ))

        OrderHistory.objects.bulk_create(order_history_objects)

    return order
