from django.core.exceptions import ObjectDoesNotExist

from apps.common.exceptions import BadStateException


def check_all_order_objects_defined(order):
    order.refresh_from_db()

    try:
        order.credit
        order.passport
        order.personal_data
        order.family_data
        order.career_education
        order.extra_data
    except ObjectDoesNotExist:
        raise BadStateException('Один из этапов не пройден')

def check_initial_payment_is_less_than_purchase_amount(order):
    if order.credit.initial_payment >= order.purchase_amount:
        raise BadStateException('Размер первоначального значения не может быть больше или равняться сумме заказа')
