from apps.common.models import Model
from django.utils.translation import gettext_lazy as __
from django.db import models as m


class MesaBank(Model):
    """ MesaBank - дополнительная модель описания банков
    Используется для обозначения взятых кредитов клиентов и банков расчётных счетов организаций
    "Mesa" - как антоним слову Meta. Имеет понижающее значение сущности на один уровень
    """
    name = m.CharField(__('Название'), max_length=150)

    class JSONAPIMeta:
        resource_name = 'mesa-banks'

    class Meta:
        indexes = [m.Index(fields=['name'])]
