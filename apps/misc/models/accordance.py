from apps.common.models import Model
from django.utils.translation import gettext_lazy as __
from django.db import models as m
from ..const import AccordanceCollection, AccordanceSpecifier
from typing import Type, Union


class Accordance(Model):
    desc = m.CharField(max_length=100)
    general = m.CharField(max_length=100, unique=True)
    specific = m.JSONField()
    collection = m.CharField(choices=AccordanceCollection.as_choices(), max_length=AccordanceCollection.length(), db_index=True)

    def __str__(self):
        return f"{self.desc} {self.collection}"

    def get_bank_value(self, bank_name: str) -> str:
        value = self.specific.get(bank_name, None)
        if value is None:
            raise self.DoesNotExist(f'Для коллекции {self.collection} не задан банк {bank_name}')
        return value

    class JSONAPIMeta:
        # Такое название для совместимости со старым API
        resource_name = 'general-accordance'
