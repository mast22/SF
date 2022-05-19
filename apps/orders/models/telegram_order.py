from django.db import models as m
from django.utils.translation import gettext_lazy as __
from apps.common.models import Model
from ..const import PhotoType

from phonenumber_field.modelfields import PhoneNumberField


class TelegramOrder(Model):
    """ Заказ из телеграмма
    Заказ из телеграмм не является полноценным заказом из-за отсутствия дополнительных данных,
    которые необходимо предоставить банку. Эти данные будут предоставлены клиентом во время
    заполнения заказа.

    Из предоставленных данных из телеграмма не заполняются:
    сумма: Сумма высчитывается по мере заполнения перечня покупаемых товаров
    номер заказа: В системе следует фигурировать только одному стандарту номера заказа
    """
    outlet = m.ForeignKey(
        'partners.Outlet',
        verbose_name=__('Торговая точка'),
        on_delete=m.DO_NOTHING,
    )
    phone = PhoneNumberField()
    created_at = m.DateTimeField()
    passport_main_photo = m.ImageField()
    passport_registry_photo = m.ImageField()
    previous_passport_photo = m.ImageField(null=True, blank=True)
    client_photo = m.ImageField()

    class JSONAPIMeta:
        resource_name = 'telegram-orders'
