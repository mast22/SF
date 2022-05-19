from decimal import Decimal
from django.db.models import F
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .order import Order
from . import OrderGood

# Нашей задачей является сохранение стоимости заказа при изменении OrderGood
@receiver(signal=pre_save, sender=OrderGood)
def pre_work_order_good_changed(sender, instance: OrderGood, *args, **kwargs):
    """ Сохраняем стоимость покупаемых товаров (размер покупки) в order
    Запускаем каждый раз чтобы сохранить стоимость товаров и изменить их в post_save
    атрибут item_sum_prev передаётся между сигналами
    """
    if instance.id:
        old_item = OrderGood.objects.get(id=instance.id)
        instance.item_sum_prev = old_item.amount * old_item.price


@receiver(signal=post_save, sender=OrderGood)
def change_order_sum_order_good_changed(sender, instance: OrderGood, created, *args, **kwargs):
    """Добавляет стоимость конкретного товара к общей сумме заказа"""
    item_sum_prev = getattr(instance, 'item_sum_prev', Decimal(0)) if not created else Decimal(0)
    item_sum = instance.amount * instance.price - item_sum_prev
    Order.objects.filter(id=instance.order_id).update(purchase_amount=F('purchase_amount') + item_sum)


@receiver(signal=post_delete, sender=OrderGood)
def change_order_sum_deleted(sender, instance: OrderGood, *args, **kwargs):
    """Вычитает стоимость конкретного товара из общей суммы заказа"""
    item_sum = instance.amount * instance.price
    Order.objects.filter(id=instance.order_id).update(purchase_amount=F('purchase_amount') - item_sum)

# # ---- Изменение поля Order.extra_services_sum при изменениях в конкретном OrderExtraService
# @receiver(signal=post_save, sender=OrderExtraService)
# def order_extra_services_changed(sender, instance: OrderExtraService, created, *args, **kwargs):
#     """Добавляет стоимость конкретной доп. услуги к общей сумме доп. услуг в заказе"""
#     Order.objects.filter(id=instance.order_id).update(extra_services_sum=F('extra_services_sum') + instance.price)
#
#
# @receiver(signal=post_delete, sender=OrderExtraService)
# def order_extra_services_delete(sender, instance: OrderExtraService, *args, **kwargs):
#     """Вычитает стоимость конкретной доп. услуги из общей суммы доп. услуг в заказе"""
#     Order.objects.filter(id=instance.order_id).update(extra_services_sum=F('extra_services_sum') - instance.price)
