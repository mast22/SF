from django.db import models as m
from django.utils.translation import gettext_lazy as __

from apps.common.models import Model
from ..const import BankBrand


class Bank(Model):
    name = m.CharField(choices=BankBrand.as_choices(), max_length=BankBrand.length(), unique=True)
    logo = m.FileField(max_length=1000)

    class JSONAPIMeta:
        resource_name = 'banks'

    class Meta:
        verbose_name = __('Банк')
        verbose_name_plural = __('Банки')
