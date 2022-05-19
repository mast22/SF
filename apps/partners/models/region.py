from django.db import models as m
from django.utils.translation import gettext_lazy as __
from apps.common.models import Model


class Region(Model):
    name = m.CharField(__('Название'), max_length=100)
    is_active = m.BooleanField(__('Активен'), default=True)
    acc_man = m.ForeignKey('users.AccMan', on_delete=m.DO_NOTHING, related_name='managed_regions')

    class JSONAPIMeta:
        resource_name = 'regions'

    class Meta:
        verbose_name = __('Регион')
        verbose_name_plural = __('Регионы')

    def __str__(self):
        return f'id:{self.id} {self.name} is_active: {self.is_active} owned by: {self.acc_man}'
