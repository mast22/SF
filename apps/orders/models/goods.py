from django.db import models as m
from django.utils.translation import gettext_lazy as __
from apps.common.models import Model
from ..const import Category


class Good(Model):
    brand = m.CharField(__('Бред/Марка'), max_length=100)
    model = m.CharField(__('Модель товара'), max_length=200)
    name = m.CharField(__('Наименование товара'), max_length=200)
    category = m.ForeignKey('misc.Accordance', verbose_name=__('Категория'), on_delete=m.DO_NOTHING)

    class JSONAPIMeta:
        resource_name = 'goods'

    def __str__(self):
        return f'Good ({self.id}). {self.name} {self.brand} {self.model} {self.category_id}'


class OrderGood(Model):
    good = m.ForeignKey('orders.Good', on_delete=m.DO_NOTHING, related_name='order_goods')
    order = m.ForeignKey('orders.Order', on_delete=m.CASCADE, related_name='goods')
    amount = m.PositiveIntegerField(default=1)
    price = m.DecimalField(__('Цена'), decimal_places=2, max_digits=12)
    serial_number = m.CharField(__('Серийный номер'), max_length=150, null=True)

    class JSONAPIMeta:
        resource_name = 'order-goods'

    def __str__(self):
        return f'OG id:({self.id}). order_id: {self.order_id}, ' \
               f'good_id: {self.good_id} {self.amount} шт. по {self.price} руб.'
