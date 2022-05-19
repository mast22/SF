import logging

from django.db.models import Prefetch
import dramatiq
from . import scoring
from .scoring import BANKS
from apps.orders.models import Order
from apps.orders.models import OrderCreditProduct

logger = logging.getLogger('scoring')


def get_order(order_id) -> Order:
    return Order.objects.prefetch_related(
        Prefetch('order_credit_products',
                 queryset=OrderCreditProduct.objects
                 .select_related('credit_product__bank')
                 .prefetch_related('extra_services').all()),
    ).get(id=order_id)


def get_ocp(order_credit_product_id) -> OrderCreditProduct:
    return OrderCreditProduct.objects.select_related('order', 'credit_product__bank').get(id=order_credit_product_id)


def send_order_to_scoring(order: Order):
    logger.info(f'Scoring started {order.id}')
    for ocp in order.order_credit_products.select_related('credit_product__bank', 'order'):
        send_to_scoring_exact_bank.send(ocp.id)


@dramatiq.actor
def send_order_to_agreement(order_id):
    order = get_order(order_id)
    scoring.send_order_to_agreement(order)


@dramatiq.actor
def send_order_client_refused(order_id):
    order = get_order(order_id)
    scoring.send_order_client_refused(order)


@dramatiq.actor
def send_order_client_refused_to_exact_bank(ocp_id):
    ocp = get_ocp(ocp_id)
    scoring.send_client_refused_exact_bank(ocp)


@dramatiq.actor
def send_order_documents(order_id):
    order = get_order(order_id)
    scoring.send_order_documents(order)


@dramatiq.actor
def send_order_to_authorization(order_id):
    order = get_order(order_id)
    scoring.send_order_to_authorization(order)


@dramatiq.actor
def send_to_scoring_exact_bank(ocp_id):
    ocp = OrderCreditProduct.objects.filter(id=ocp_id).select_related('credit_product__bank', 'order')
    bank = ocp.credit_product.bank
    order = ocp.order
    bank_provider_class = BANKS[bank.name]
    bank_provider = bank_provider_class(ocp, bank, order)
    bank_provider.send_to_scoring()
    send_to_scoring_exact_bank.logger.info(f'Scoring for bank {bank.name} started. OCP id: {ocp.id}')


@dramatiq.actor
def send_client_refused_exact_bank(ocp_id):
    ocp = get_ocp(ocp_id)
    scoring.send_client_refused_exact_bank(ocp)


# Импортируем таски для конкретных банков.
from apps.banks_app.pochta.updaters.tasks import *
