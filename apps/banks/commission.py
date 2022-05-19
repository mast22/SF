from decimal import Decimal
from django.utils.translation import gettext as _

from apps.common.utils import xor
from apps.orders.models.order import Order
from . import const as c
from . import models as m


# def get_order_staff(agent, order: Order, credit_product: m.CreditProduct, first_payment: Decimal, term: int):
#     order_sum = order.purchase_amount if order.purchase_amount else Decimal(0)
#     anal_rate = credit_product.annual_rate if credit_product.annual_rate else Decimal(0)
#     first_payment = first_payment if first_payment else Decimal(0)
#     term = term if term else 1
#     monthly_payment, overpayment = calculate_monthly_and_over_payment(order_sum, anal_rate, first_payment, term)
#     agent_commission = agent_credit_product_commission(agent, order, credit_product)
#     return monthly_payment, overpayment, agent_commission


def calculate_monthly_and_over_payment(
        order_sum: Decimal=Decimal(0),
        annual_rate: Decimal=Decimal(0),
        first_payment: Decimal=Decimal(0),
        term: int=1):
    """Рассчитывает ежемесячный платёж и переплату по кредиту"""
    rate = (annual_rate * term) / (12 * 100)
    purchase_amount = order_sum - first_payment
    overpayment = purchase_amount * rate
    monthly_payment = (purchase_amount + overpayment) / term
    return monthly_payment, overpayment


def calculate_agent_commissions_chosen_product(order):
    """Вычисляет комиссию агента за заказ, у которого выбран кредитный продукт."""
    # Процент агента
    cp_agent_commission = get_agent_credit_product_commission(order, order.chosen_product.credit_product)
    es_agent_commission = Decimal(0)
    for es in order.chosen_product.order_extra_services.select_related('extra_service').all():
        es_agent_commission += get_agent_extra_service_commission(order, es.extra_service)
    return cp_agent_commission, es_agent_commission


def get_agent_credit_product_commission(order: Order, credit_product: m.CreditProduct) -> Decimal:
    """Вычисляет комиссию агента за заданный кредитный продукт.
    :param Order order: заявка,
    :param CreditProduct credit_product: кредитный продукт
    :return Decimal: комиссия агента (в рублях)
    """
    acp = m.AgentCreditProduct.objects.get(credit_product_id=credit_product.id, agent_bank__agent_id=order.agent_id)
    if acp.commission is None:
        # У агента не задана его собственная комиссия, теперь это - недопустимая ситуация, вызываем Exception
        raise ValueError(f'Для агента {order.agent} не назначена комиссия на КП {credit_product}')
    # Вычисляем сумму в рублях как процент от суммы, взятой в кредит (за вычетом первоначального взноса)
    agent_commission = order.get_credit_sum() * acp.commission
    return agent_commission


def get_agent_extra_service_commission(order: Order, extra_service: m.ExtraService) -> Decimal:
    """Вычисляет сумму, получаемую агентом за доп. услуги.
    :param Order order: заявка,
    :param ExtraService extra_service: Доп. услуга
    :return Decimal: комиссия агента (в рублях)
    """
    aes = m.AgentExtraService.objects.get(agent_bank__agent_id=order.agent_id, extra_service_id=extra_service.id)
    if aes.agent_commission is None:
        # У агента не задана его комиссия за доп. услугу, недопустимая ситуёвина.
        raise ValueError(f'There is no commission for agent {order.agent} and extra service {extra_service}')
    if extra_service.price_type == c.ExtraServicePriceType.CURRENCY:
        agent_commission = extra_service.price * aes.commission
    elif extra_service.price_type == c.ExtraServicePriceType.PERCENT:
        credit_sum = order.get_credit_sum()
        agent_commission = credit_sum * extra_service.price * aes.commission
    else:
        raise ValueError(f'Wrong extra_service {extra_service}')
    return agent_commission


def get_terman_credit_product_commission(order: Order, credit_product: m.CreditProduct) -> Decimal:
    """Вычисляет сумму, получаемую территориальным менеджером за кредитный продукт"""
    tcp = m.TerManCreditProduct.objects.get(
        credit_product_id=credit_product.id,
        terman_bank__ter_man__agents__id=order.agent_id)
    if tcp.commission is None:
        # У агента не задана его собственная комиссия, теперь это - недопустимая ситуация, вызываем Exception
        raise ValueError(f'Для территориала {order.agent.ter_man} не назначена комиссия на КП {credit_product}')
    # Вычисляем сумму в рублях как процент от суммы, взятой в кредит (за вычетом первоначального взноса)
    terman_commission = order.get_credit_sum() * tcp.commission
    return terman_commission


def get_terman_extra_service_commission(order: Order, extra_service: m.ExtraService) -> Decimal:
    """Вычисляет сумму, получаемую территориальным менеджером за доп. услуги"""
    tes = m.TerManExtraService.objects.get(
        terman_bank__ter_man__agents__id=order.agent_id,
        extra_service_id=extra_service.id)
    if tes.agent_commission is None:
        # У агента не задана его комиссия за доп. услугу, недопустимая ситуёвина.
        raise ValueError(f'Для территориала {order.agent.ter_man} не назначена комиссия на Доп. {extra_service}')
    if extra_service.price_type == c.ExtraServicePriceType.CURRENCY:
        terman_commission = extra_service.price * tes.commission
    elif extra_service.price_type == c.ExtraServicePriceType.PERCENT:
        credit_sum = order.get_credit_sum()
        terman_commission = credit_sum * extra_service.price * tes.commission
    else:
        raise ValueError(f'Wrong extra_service {extra_service}')
    return terman_commission



def check_for_min_max(commission: Decimal,
            credit_product: m.CreditProduct=None,
            extra_service: m.ExtraService=None,
            agent_bank: m.AgentBank=None,
            # outlet_bank: m.OutletBank=None,
            **__):
    """Проверяет комиссию агента на пределы от-до"""
    if not commission:
        return False, _('Поле commission не может быть пустым или нулём!')
    commission_min, commission_max = get_min_max(credit_product=credit_product,
        extra_service=extra_service, agent_bank=agent_bank)

    result, msg = True, None
    if commission_min and commission < commission_min:
        result, msg = False, _(f'Комиссия агента не может быть меньше, чем {commission_min}!')
    elif commission_max and commission > commission_max:
        result, msg = False, _(f'Комиссия агента не может быть больше, чем {commission_max}!')
    return result, msg


def get_min_max(
            credit_product: m.CreditProduct=None,
            extra_service: m.ExtraService=None,
            agent_bank: m.AgentBank=None,
            outlet_bank: m.OutletBank=None,
    ):
    """Достаёт минимальную и максимальную комиссии для заданного набора параметров"""
    assert xor(credit_product, extra_service), _('Одно и только одно из credit_product, extra_service должно быть задано')

    is_cp = credit_product is not None and extra_service is None
    is_ab = agent_bank is not None and outlet_bank is None
    cp_or_es_arg = credit_product if is_cp else extra_service
    ab_or_ob_arg = agent_bank if is_ab else outlet_bank

    klasses = {
        (True, True): (m.CreditProduct, m.TerManCreditProduct, 'agent_bank', 'credit_product'),
        (True, False): (m.ExtraService, m.TerManExtraService, 'outlet_bank', 'extra_services'),
    }
    cp_class, allowed_class, ab_field, cp_field = klasses[(is_cp, is_ab)]

    limits_instance = allowed_class.objects.filter(**{
        ab_field: ab_or_ob_arg,
        cp_field: cp_or_es_arg,
    }).first()
    if limits_instance is None:
        commission_min, commission_max = limits_instance.commission_min, limits_instance.commission_max
    else:
        commission_min, commission_max = cp_or_es_arg.commission_min, cp_or_es_arg.commission_max
    return commission_min, commission_max


def get_min_max_agent_bank(agent_bank):
    return None, None




def get_commissions_for_order(order: Order):
    """Вытаскивает комиссию, которую получит агент за заказ"""
    agent_commissions = m.AgentCreditProduct.objects.filter(
        agent_id=order.agent_id,
        outlet_id=order.outlet_id,
        credit_product__in=order.credit_products.all(),
        is_active=True,
    )
    cp_results = {}
    for ag_com in agent_commissions:
        cp_id = ag_com.credit_product_id
        cp_results[cp_id] = ag_com.commission

    agent_commissions = m.AgentExtraService.objects.filter(
        agent_id=order.agent_id,
        outlet_id=order.outlet_id,
        extra_service__in=order.extra_services.all(),
    )
    ex_s_results = {}
    for ag_com in agent_commissions:
        exs_id = ag_com.extra_service_id
        ex_s_results[exs_id] = ag_com.commission
    return cp_results, ex_s_results




