from django.db import models as m
from apps.common.models import Model
from django.utils.translation import gettext_lazy as __
from apps.partners.const import REGION_CHOICES
from apps.partners.const import LocalityType


class Location(Model):
    """Адрес."""
    street = m.CharField(__('Улица, проспект, шоссе, переулок'), max_length=100)
    house = m.CharField(__('Дом'), max_length=100)
    block = m.CharField(__('Корпус'), max_length=100, null=True)
    building = m.CharField(__('Строение'), max_length=100, null=True)
    place = m.CharField(__('Офис/Квартира'), max_length=100, null=True)
    postcode = m.CharField(__('Индекс'), max_length=6)
    subject = m.IntegerField(choices=REGION_CHOICES, verbose_name=__('Субъект РФ'))
    type = m.CharField(
        __('Тип населенного пункта'),
        choices=LocalityType.as_choices(),
        max_length=LocalityType.length()
    )
    locality = m.CharField(__('Название населенного пункта'), max_length=100)

    def to_human(self):
        return f'нас. п. {self.locality}, {self.street} д. {self.house}' \
               f'{" корп." + self.block if self.block else ""}' \
               f'{" стр." + self.building if self.building else ""}' \
               f'{" кв./офис " + self.building if self.building else ""}'

    class JSONAPIMeta:
        resource_name = 'locations'
