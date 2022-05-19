from django.db import models as m
from django.utils.translation import gettext_lazy as __
from phonenumber_field.modelfields import PhoneNumberField
from apps.common.models import Model
from apps.users.models.user import TerMan
from .region import Region


class Partner(Model):
    region = m.ForeignKey(Region, on_delete=m.CASCADE, related_name='partners')
    ter_man = m.ForeignKey(TerMan, on_delete=m.CASCADE, related_name='partners')

    is_active = m.BooleanField(__('Активен'), default=True)
    name = m.CharField(__('Наименование'), max_length=120)
    legal_name = m.CharField(__('Официальное наименовение'), max_length=250)
    phone = PhoneNumberField(__('Телефон'))
    email = m.EmailField('Email')

    TIN = m.CharField(__('ИНН'), max_length=12)
    PSRN = m.CharField(__('ОГРН'), max_length=15)
    IEC = m.CharField(__('КПП'), max_length=9, null=True)
    CA = m.CharField(__('Корреспондентский счёт'), max_length=20)
    giro = m.CharField(__('Расчётный счёт'), max_length=20)
    RCBIC = m.CharField(__('БИК'), max_length=9)
    bank = m.ForeignKey('misc.MesaBank', on_delete=m.DO_NOTHING, null=True)

    actual_address = m.OneToOneField(
        'partners.Location',
        verbose_name=__('Фактический адрес'),
        on_delete=m.DO_NOTHING,
        related_name='+',
    )
    legal_address = m.OneToOneField(
        'partners.Location',
        verbose_name=__('Юридический адрес'),
        on_delete=m.DO_NOTHING,
        related_name='+'
    )

    class JSONAPIMeta:
        resource_name = 'partners'

    class Meta:
        verbose_name = __('Партнёр')
        verbose_name_plural = __('Партнёры')


class PartnerBank(Model):
    bank = m.ForeignKey('banks.Bank', on_delete=m.DO_NOTHING, related_name='partner_banks')
    partner = m.ForeignKey(Partner, on_delete=m.DO_NOTHING, related_name='partner_banks')
    is_active = m.BooleanField(default=True)
    code = m.CharField(max_length=100)

    class JSONAPIMeta:
        resource_name = 'partner-banks'

    class Meta:
        verbose_name = __('Связь партнёра и банка')
        verbose_name_plural = __('Связи партнёров и банков')
