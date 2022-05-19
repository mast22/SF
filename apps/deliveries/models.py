from django.db import models as m
from django.utils.translation import gettext_lazy as __

from apps.common.models import Model, SingleRowModel
from apps.deliveries.const import ContractLocation


class Delivery(Model):
    """ Отправка документов """
    cdek_uuid = m.UUIDField(__('Номер заказа СДЭК'), max_length=100, null=True)
    location = m.CharField(
        choices=ContractLocation.as_choices(),
        default=ContractLocation.IN_OUTLET,
        null=True,
        max_length=ContractLocation.length()
    )
    last_modified = m.DateTimeField(__('Последнее изменение'), auto_now=True)

    class JSONAPIMeta:
        resource_name = 'deliveries'


class CdekToken(SingleRowModel):
    """ Токен создаётся по авторизации в системе СДЭК """

    class JSONAPIMeta:
        resource_name = 'cdek-tokens'
