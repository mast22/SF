from django.utils.translation import gettext_lazy as __
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models as m
from apps.common.models import Model


class Client(Model):
    """Клиент."""
    phone = PhoneNumberField(__('Телефон'))
    created_at = m.DateTimeField(__('Дата создания'), auto_now_add=True)
    is_active = m.BooleanField(__('Активен'), default=True)

    def __str__(self):
        return f'Client {self.phone} {"Active" if self.is_active else "Inactive"} created_at: {self.created_at}'

    class Meta:
        verbose_name = __('Клиент')
        verbose_name_plural = __('Клиенты')

    class JSONAPIMeta:
        resource_name = 'clients'


class ClientOrder(Model):
    """Связь клиента с конкретным заказом"""
    client = m.ForeignKey(Client, on_delete=m.SET_NULL, null=True, related_name='client_orders')
    phone = PhoneNumberField(__('Телефон'))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.phone:
            self.phone = self.client.phone
        return super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f'ClientOrder. {self.client} for order: {self.order}'

    class Meta:
        verbose_name = __('Клиент в заказе')
        verbose_name_plural = __('Клиенты в заказах')

    class JSONAPIMeta:
        resource_name = 'client-orders'
