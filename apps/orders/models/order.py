from decimal import Decimal
from django.db import models as m
from django.utils.translation import gettext_lazy as __
# from rest_framework_json_api import serializers as s
# from django.core.exceptions import ObjectDoesNotExist

from apps.common.models import Model
from apps.partners.models import Outlet
from apps.banks.models import CreditProduct
from .. import const as c
from ..const import CreditProductStatus
from ..workflows import OrderStatusFSM


class Order(OrderStatusFSM, Model):
    """ Заказ на получение кредита """
    # noinspection PyUnresolvedReferences
    client_order = m.OneToOneField('orders.ClientOrder', on_delete=m.DO_NOTHING, related_name='order')
    # noinspection PyUnresolvedReferences
    agent = m.ForeignKey('users.Agent', on_delete=m.DO_NOTHING, related_name='orders')
    outlet = m.ForeignKey(Outlet, on_delete=m.DO_NOTHING, related_name='orders')

    status = m.CharField(
        verbose_name=__('Статус'),
        choices=c.OrderStatus.as_choices(),
        default=c.OrderStatus.NEW,
        max_length=c.OrderStatus.length()
    )
    created_at = m.DateTimeField(verbose_name=__('Дата и время создания'), auto_now_add=True)
    changed_at = m.DateTimeField(verbose_name=__('Дата и время изменения'), auto_now=True)
    chosen_product = m.ForeignKey('OrderCreditProduct', on_delete=m.SET_NULL, null=True, related_name='orders_chosen')

    # noinspection PyUnresolvedReferences
    credit_products = m.ManyToManyField(CreditProduct, related_name='orders_pre', through='orders.OrderCreditProduct')
    # noinspection PyUnresolvedReferences
    # extra_services = m.ManyToManyField(ExtraService, related_name='orders', through='orders.OrderExtraService')

    # noinspection PyUnresolvedReferences
    telegram_order = m.OneToOneField('orders.TelegramOrder', on_delete=m.CASCADE, null=True, related_name='order')
    # purchase_amount заполняется либо запросом либо сигналами
    purchase_amount = m.DecimalField(__('Сумма покупки'), max_digits=12, decimal_places=2, default=0)
    agent_commission_sum = m.DecimalField(__('Комиссия агента'), max_digits=12, decimal_places=2, default=0)
    reject_reason = m.CharField(__('Причина отказа от кредита'), choices=c.RejectReason.as_choices(),
                                default=c.RejectReason.NO_EXPLANATION, max_length=c.RejectReason.length())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_error = None

    def change_status_history(self, new_status):
        self.history.create(order_status=new_status, description=self.status_error)

    def get_credit_sum(self):
        return (self.purchase_amount - self.credit.initial_payment) if self.purchase_amount is not None else Decimal(0)

    def has_ever_been_scored(self) -> bool:
        """ Был ли когда-нибудь заказ отправлен на скоринг
        Если заказ был отправлен на скоринг, то у него есть OCP со статусами не "новый"
        """
        return self.order_credit_products.filter(~m.Q(status=CreditProductStatus.NOT_SENT)).exists()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.id is None and self.purchase_amount is None:
            self.purchase_amount = 0

        # Выбираем предыдущий статус заказа перед сохранением (если есть):
        order_status = Order.objects.filter(pk=self.pk).values_list('status').first() if self.pk else None

        super(Order, self).save(force_insert=force_insert, force_update=force_update,
                                using=using, update_fields=update_fields)

        # Сохраняем в историю изменение статуса заказа
        if self.status != order_status:
            self.change_status_history(self.status)

    class JSONAPIMeta:
        resource_name = 'orders'
