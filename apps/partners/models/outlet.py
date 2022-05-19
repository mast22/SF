from django.db import models as m
from django.db.models import Model
from django.utils.translation import gettext_lazy as __
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError
from .. import const as c


# noinspection PyUnresolvedReferences
class Outlet(Model):
    partner = m.ForeignKey('partners.Partner', on_delete=m.CASCADE, related_name='outlets')
    banks = m.ManyToManyField(to='banks.Bank', related_name='outlets', through='banks.OutletBank')
    agents = m.ManyToManyField(to='users.Agent', related_name='outlets', through='OutletAgent')

    name = m.CharField(__('Наименование торговой точки'), max_length=100)
    address = m.ForeignKey('partners.Location', on_delete=m.CASCADE)
    phone = PhoneNumberField(__('Телефон'), null=True, blank=True)
    email = m.EmailField(__('Email'), null=True, blank=True)
    status = m.CharField(__('Статус'), choices=c.OutletStatus.as_choices(), default=c.OutletStatus.ACTIVE,
            max_length=c.OutletStatus.length())
    telegram_id = m.CharField(__('Идентификатор торговой точки в боте'),
        max_length=250, null=True, unique=True, blank=True
    )

    # def clean(self):
    #     if self.partner.region != self.region:
    #         # Проверяем, что у ТТ и партнера одинаковые регионы
    #         raise ValidationError('У партнера и торговой точки должны быть одинаковые регионы')
    #
    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
    #     self.full_clean()
    #     super(Outlet, self).save(force_insert, force_update, using, update_fields)

    @property
    def is_active(self):
        return self.status == c.OutletStatus.ACTIVE

    class JSONAPIMeta:
        resource_name = 'outlets'

    class Meta:
        verbose_name = __('Торговая точка')
        verbose_name_plural = __('Торговые точки')


class OutletAgent(Model):
    # noinspection PyUnresolvedReferences
    agent = m.ForeignKey('users.Agent', on_delete=m.CASCADE, related_name='outlet_agents')
    outlet = m.ForeignKey(Outlet, on_delete=m.CASCADE, related_name='outlet_agents')
    is_active = m.BooleanField(default=True)

    class JSONAPIMeta:
        resource_name = 'outlet-agents'

    class Meta:
        unique_together = ('agent', 'outlet')
        verbose_name = __('Связь торговой точки с агентом')
        verbose_name_plural = __('Связи торговых точек с агентами')
