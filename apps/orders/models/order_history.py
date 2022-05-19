from django.db import models as m
from django.utils.translation import gettext_lazy as __
from apps.common.models import Model
from .order import Order
from .. import const as c


class OrderHistory(Model):
    """ История статусов заказа """
    order = m.ForeignKey(Order, on_delete=m.CASCADE, related_name='history')
    credit_product = m.ForeignKey('orders.OrderCreditProduct', on_delete=m.CASCADE, related_name='history', null=True)
    order_status = m.CharField(
        verbose_name=__('Статус заявки'),
        choices=c.OrderStatus.as_choices(),
        default=c.OrderStatus.NEW,
        max_length=c.OrderStatus.length()
    )
    credit_product_status = m.CharField(
        verbose_name=__('Статус кредитного продукта'),
        choices=c.CreditProductStatus.as_choices(),
        max_length=c.CreditProductStatus.length(),
        null=True,
    )
    description = m.TextField(__('Подробности'), default='', null=True)
    changed_at = m.DateTimeField(verbose_name=__('Изменен в'), auto_now_add=True)

    def __str__(self):
        return f'OrderStatusHistory ({self.id}). status: {self.order_status} at {self.changed_at}'

    class JSONAPIMeta:
        resource_name = 'order-history'
