from django.db import models as m

from apps.common.models import Model
from django.utils.translation import gettext_lazy as __

from ..const import ExtraServiceType, ExtraServicePriceType
from . import Bank


class CreditProduct(Model):
    """Кредитный продукт банка"""
    bank = m.ForeignKey(Bank, on_delete=m.CASCADE, related_name='credit_products')
    name = m.CharField(__('Наименование'), max_length=200)

    # TODO поля будут зависеть от данных предоставляемых банками
    total_min = m.DecimalField(__('Сумма. От'), decimal_places=2, max_digits=12)
    total_max = m.DecimalField(__('Сумма. До'), decimal_places=2, max_digits=12)

    term_min = m.PositiveSmallIntegerField(__('Срок. От'))
    term_max = m.PositiveSmallIntegerField(__('Срок. До'))

    initial_payment_min = m.DecimalField(__('Первоначальный взнос. От'), decimal_places=2, max_digits=10)
    initial_payment_max = m.DecimalField(__('Первоначальный взнос. До'), decimal_places=2, max_digits=10)

    annual_rate = m.DecimalField(__('Годовой процент'), decimal_places=2, max_digits=5)

    is_active = m.BooleanField(__('Доступен'), default=True)

    code = m.CharField(__('Код в банке'), max_length=200, null=True)

    def __str__(self):
        return f'{self.id} Bank:{self.bank_id} Active:{self.is_active} Code: {self.code}'

    class JSONAPIMeta:
        resource_name = 'credit-products'



class ExtraService(Model):
    """Дополнительные услуги банка"""
    bank = m.ForeignKey(Bank, on_delete=m.CASCADE, related_name='extra_services')
    type = m.CharField(__('Тип доп. услуги'), choices=ExtraServiceType.as_choices(),
            max_length=ExtraServiceType.length(), default=ExtraServiceType.CUSTOM)
    price_type = m.CharField(__('Тип цены'), choices=ExtraServicePriceType.as_choices(),
            max_length=ExtraServicePriceType.length(), default=ExtraServicePriceType.PERCENT)
    name = m.CharField(__('Наименование'), max_length=200)
    price = m.DecimalField(__('Стоимость'), decimal_places=2, max_digits=10)
    is_active = m.BooleanField(__('Доступен'), default=True)

    class JSONAPIMeta:
        resource_name = 'extra-services'
