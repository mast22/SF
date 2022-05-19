from decimal import Decimal
from django.db import models as m
from django.utils.translation import gettext_lazy as __
from django.core.exceptions import ValidationError
from apps.common.models import Model
from apps.users.models.user import Agent, TerMan
from apps.users.const import Roles
from apps.partners.models import Outlet
from . import Bank, CreditProduct, ExtraService
from ..const import BankPriorityChoice


class TerManBank(Model):
    """ Доступность тер.манагера взаимодействия с банком """
    bank = m.ForeignKey(Bank, on_delete=m.CASCADE, related_name='terman_banks')
    ter_man = m.ForeignKey(TerMan, on_delete=m.CASCADE, related_name='terman_banks')
    is_active = m.BooleanField(__('Активен'), default=True)
    priority = m.PositiveSmallIntegerField(__('Приоритет банка'),
            choices=BankPriorityChoice.as_choices(), default=BankPriorityChoice.FIRST)

    class JSONAPIMeta:
        resource_name = 'terman-banks'

    class Meta:
        verbose_name = __('Связь территориального менеджера с банком')
        verbose_name_plural = __('Связи территориальных менеджеров с банками')
        unique_together = ('bank', 'ter_man')



class TerManCreditProduct(Model):
    """Допустимая комиссия за кредитный продукт для территориала."""
    terman_bank = m.ForeignKey(TerManBank, on_delete=m.CASCADE, related_name='terman_credit_products')
    credit_product = m.ForeignKey(CreditProduct, on_delete=m.CASCADE, related_name='terman_credit_products')
    is_active = m.BooleanField(__('Доступность'), default=True)
    commission = m.DecimalField(__('Комиссия территориала'), max_digits=5, decimal_places=2, default=Decimal(0))
    commission_min = m.DecimalField(__('Комиссия агентов. От'), max_digits=5, decimal_places=2)
    commission_max = m.DecimalField(__('Комиссия агентов. До'), max_digits=5, decimal_places=2)

    class JSONAPIMeta:
        resource_name = 'terman-credit-products'

    class Meta:
        verbose_name = __('Настройки и комиссия за кредитный продукт для территориала')
        unique_together = ('terman_bank', 'credit_product')
        constraints = [m.constraints.CheckConstraint(
                name='terman_creditproducts_commission_min_is_less_than_max',
                check=m.Q(commission_min__lte=m.F('commission_max'))
        )]


class TerManExtraService(Model):
    """Допустимая комиссия за доп. услуги для территориала."""
    terman_bank = m.ForeignKey(TerManBank, on_delete=m.CASCADE, related_name='terman_extra_services')
    extra_service = m.ForeignKey(ExtraService, on_delete=m.CASCADE, related_name='terman_extra_services')
    is_active = m.BooleanField(__('Доступность'), default=True)
    commission = m.DecimalField(__('Комиссия территориала'), max_digits=5, decimal_places=2, default=Decimal(0))
    commission_min = m.DecimalField(__('Комиссия. От'), max_digits=5, decimal_places=2)
    commission_max = m.DecimalField(__('Комиссия. До'), max_digits=5, decimal_places=2)

    class JSONAPIMeta:
        resource_name = 'terman-extra-services'

    class Meta:
        verbose_name = __('Настройки и комиссия за доп. услугу для территориала')
        unique_together = ('terman_bank', 'extra_service')
        constraints = [
            m.constraints.CheckConstraint(
                name='terman_extra_services_commission_min_is_less_than_max',
                check=m.Q(commission_min__lte=m.F('commission_max'))
            )
        ]


class AgentBank(Model):
    """ Доступность агента взаимодействия с банком """
    bank = m.ForeignKey(Bank, on_delete=m.CASCADE, related_name='agent_banks', blank=True)
    agent = m.ForeignKey(Agent, on_delete=m.CASCADE, related_name='agent_banks')
    terman_bank = m.ForeignKey(TerManBank, on_delete=m.CASCADE, related_name='agent_banks')
    is_active = m.BooleanField(__('Активен'), default=True)
    code = m.CharField(__('Код агента в банке'), max_length=150, null=True, blank=True)

    def clean(self):
        if self.agent.role != Roles.AGENT:
            raise ValidationError(f'AgentBank.agent need to be an agent, got: {self.agent.role}: {self.agent}')
        if self.terman_bank.bank_id != self.bank_id:
            raise ValidationError(f'AgentBank.terman_bank is wrong! {self.bank} but {self.terman_bank}')
        if self.terman_bank.ter_man != self.agent.ter_man:
            raise ValidationError(f'Тер. менеджер terman_bank не такой-же как тер. менеджер у агента')
        if self.is_active and not self.terman_bank.is_active:
            raise ValidationError(f'AgentBank.terman_bank is not active, cant set agent_bank as active')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.terman_bank_id and not self.bank_id:
            self.bank_id = self.terman_bank.bank_id
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'AgentBank. Agent: {self.agent_id}, Bank: {self.bank_id} (is_active: {self.is_active}, code: {self.code})'

    class JSONAPIMeta:
        resource_name = 'agent-banks'

    class Meta:
        verbose_name = __('Связь агента с банком')
        verbose_name_plural = __('Связи агентов с банками')
        unique_together = ('bank', 'agent')
        # constraints = [m.constraints.CheckConstraint(
        #         name='agent_bank_commission_min_is_less_than_max',
        #         check=m.Q(commission_min__isnull=True)|m.Q(commission_min__lte=m.F('commission_max'))
        # )]


class AgentCreditProduct(Model):
    """Кредитные продукты агента с комиссией, применяемой к агенту и доступностью его использования"""
    credit_product = m.ForeignKey(CreditProduct, on_delete=m.CASCADE, related_name='agent_credit_products', blank=True)
    agent_bank = m.ForeignKey(AgentBank, on_delete=m.CASCADE, related_name='agent_credit_products')
    terman_credit_product = m.ForeignKey(TerManCreditProduct, on_delete=m.CASCADE, related_name='agent_credit_products')
    commission = m.DecimalField(verbose_name=__('Комиссия'), decimal_places=2, max_digits=5)
    is_active = m.BooleanField(__('Доступность'), default=True)

    def clean(self):
        if self.credit_product.bank_id != self.agent_bank.bank_id:
            raise ValidationError(f'Wrong credit product: {self.credit_product} for agent_bank: {self.agent_bank}')
        if self.terman_credit_product_id:
            if self.terman_credit_product.credit_product_id != self.credit_product_id:
                raise ValidationError(f'Wrong credit product: {self.credit_product} for terman_credit_product: {self.terman_credit_product}')
            if self.terman_credit_product.terman_bank.bank_id != self.agent_bank.bank_id:
                raise ValidationError(f'Wrong bank_id: {self.agent_bank.bank_id} for terman_credit_product: {self.terman_credit_product}')
            if self.terman_credit_product.terman_bank.ter_man_id != self.agent_bank.agent.ter_man_id:
                raise ValidationError(f'Wrong credit product: {self.credit_product} for terman_credit_product: {self.terman_credit_product}')
            if self.is_active and not self.terman_credit_product.is_active:
                raise ValidationError(f'AgentCreditProduct cant be active while TerManCreditProduct is not')

    def _get_credit_product(self):
        return self.terman_credit_product.credit_product

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.terman_credit_product_id and not self.credit_product_id:
            self.credit_product = self._get_credit_product()
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'AgentCreditProduct. AgentBank: {self.agent_bank_id}, CreditProduct: {self.credit_product_id},' \
               f' commission: {self.commission} (is_active: {self.is_active})'

    class JSONAPIMeta:
        resource_name = 'agent-credit-products'

    class Meta:
        unique_together = ('agent_bank', 'credit_product')
        verbose_name = __('Настройки кредитного продукта для агента')
        verbose_name_plural = __('Настройки кредитных продуктов для агента')


class AgentExtraService(Model):
    """Настройки дополнительных услуг банка для агента"""
    extra_service = m.ForeignKey(ExtraService, on_delete=m.CASCADE, related_name='agent_extra_services', blank=True)
    agent_bank = m.ForeignKey(AgentBank, on_delete=m.CASCADE, related_name='agent_extra_services')
    terman_extra_service = m.ForeignKey(TerManExtraService, on_delete=m.CASCADE, related_name='agent_extra_services')
    commission = m.DecimalField(verbose_name=__('Комиссия'), decimal_places=2, max_digits=5)
    is_active = m.BooleanField(__('Доступность'), default=True)

    def clean(self):
        if self.extra_service.bank_id != self.agent_bank.bank_id:
            raise ValidationError(f'Wrong extra_service: {self.extra_service} for agent_bank: {self.agent_bank}')
        if self.terman_extra_service_id:
            if self.terman_extra_service.extra_service_id != self.extra_service_id:
                raise ValidationError(f'Wrong extra_service: {self.extra_service_id} for terman_extra_service: {self.terman_extra_service}')
            if self.terman_extra_service.terman_bank.bank_id != self.agent_bank.bank_id:
                raise ValidationError(f'Wrong bank_id: {self.agent_bank.bank_id} for terman_extra_service: {self.terman_extra_service}')
            if self.terman_extra_service.terman_bank.ter_man_id != self.agent_bank.agent.ter_man_id:
                raise ValidationError(f'Wrong extra_service: {self.extra_service_id} for terman_extra_service: {self.terman_extra_service}')

    def _get_extra_service(self):
        return self.terman_extra_service.extra_service

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.terman_extra_service_id and not self.extra_service_id:
            self.extra_service = self._get_extra_service()
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'AgentExtraService. AgentBank: {self.agent_bank_id}, ExtraService: {self.extra_service_id},' \
               f' (commission: {self.commission} is_active: {self.is_active})'

    class JSONAPIMeta:
        resource_name = 'agent-extra-services'

    class Meta:
        unique_together = ('agent_bank', 'extra_service')
        verbose_name = __('Настройки доп. услуги для агента')
        verbose_name_plural = __('Настройки доп. услуг для агента')



class OutletBank(Model):
    """Настройки торговой точки для банка"""
    bank = m.ForeignKey(Bank, on_delete=m.DO_NOTHING, related_name='outlet_banks')
    outlet = m.ForeignKey(Outlet, on_delete=m.CASCADE, related_name='outlet_banks')
    is_active = m.BooleanField(default=True)
    code = m.CharField(max_length=100, null=True)

    def __str__(self):
        return f'OutletBank. Outlet: {self.outlet_id}, Bank: {self.bank_id} (is_active: {self.is_active}, code: {self.code})'

    class JSONAPIMeta:
        resource_name = 'outlet-banks'

    class Meta:
        verbose_name = __('Связь торговой точки и банка')
        verbose_name_plural = __('Связи торговых точек и банков')
        unique_together = ('bank', 'outlet')
        # constraints = [m.constraints.CheckConstraint(
        #         name='outlet_bank_commission_min_is_less_than_max',
        #         check=m.Q(commission_min__isnull=True)|m.Q(commission_min__lte=m.F('commission_max'))
        # )]


class OutletCreditProduct(Model):
    """
    Кредитные продукты агента с комиссией, применяемой к агенту и доступностью его использования
    """
    credit_product = m.ForeignKey(CreditProduct, on_delete=m.CASCADE, related_name='outlet_credit_products')
    outlet_bank = m.ForeignKey(OutletBank, on_delete=m.CASCADE, related_name='outlet_credit_products')
    is_active = m.BooleanField(__('Доступность'), default=True)

    def clean(self):
        if self.credit_product.bank_id != self.outlet_bank.bank_id:
            raise ValidationError(f'Wrong credit product: {self.credit_product} for agent_bank: {self.outlet_bank}')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'OutletCreditProduct OB: {self.outlet_bank.id}, CP: {self.credit_product.id}'

    class JSONAPIMeta:
        resource_name = 'outlet-credit-products'

    class Meta:
        unique_together = ('outlet_bank', 'credit_product')
        verbose_name = __('Настройки кредитного продукта для торговой точки')
        verbose_name_plural = __('Настройки кредитных продуктов для торговых точек')


class OutletExtraService(Model):
    """
    Кредитные продукты агента с комиссией, применяемой к агенту и доступностью его использования
    """
    extra_service = m.ForeignKey(ExtraService, on_delete=m.CASCADE, related_name='outlet_extra_services')
    outlet_bank = m.ForeignKey(OutletBank, on_delete=m.CASCADE, related_name='outlet_extra_services')
    is_active = m.BooleanField(__('Доступность'), default=True)

    def clean(self):
        if self.extra_service.bank_id != self.outlet_bank.bank_id:
            raise ValidationError(f'Wrong credit product: {self.extra_service} for agent_bank: {self.outlet_bank}')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'OutletExtraService. OutletBank: {self.outlet_bank}, ExtraService: {self.extra_service},' \
               f' (is_active: {self.is_active})'

    class JSONAPIMeta:
        resource_name = 'outlet-extra-services'

    class Meta:
        unique_together = ('outlet_bank', 'extra_service')
        verbose_name = __('Настройки дополнительной услуги для торговой точки')
        verbose_name_plural = __('Настройки дополнительных услуг для торговых точек')

#
# class AgentOutletCreditProduct(Model):
#     """Кредитные продукты торговой точки с комиссией, применяемой к агенту на данной торговой точке."""
#     agent_bank = m.ForeignKey(AgentBank, on_delete=m.CASCADE, related_name='%(class)ss')
#     outlet_bank = m.ForeignKey(Outlet, on_delete=m.CASCADE, related_name='agent_outlet_credit_products')
#     credit_product = m.ForeignKey(CreditProduct, on_delete=m.CASCADE, related_name='agent_outlet_credit_products')
#     commission = m.DecimalField(__('Комиссия'), decimal_places=1, max_digits=2)
#     is_active = m.BooleanField(__('Доступность'), default=True)
#
#     class JSONAPIMeta:
#         resource_name = 'agent-outlet-credit-products'
#
#     class Meta:
#         unique_together = ('agent_bank', 'outlet_bank', 'credit_product')
#         verbose_name = __('Настройки кредитного продукта агента по торговой точке')
#         verbose_name_plural = __('Настройки кредитных продуктов агентов по торговым точкам')
#
#
# class AgentOutletExtraService(Model):
#     """Дополнительные услуги торговой точки
#     """
#     agent_bank = m.ForeignKey(AgentBank, on_delete=m.CASCADE, related_name='%(class)ss')
#     extra_service = m.ForeignKey(ExtraService, on_delete=m.CASCADE, related_name='agent_outlet_extra_services')
#     outlet_bank = m.ForeignKey(Outlet, on_delete=m.CASCADE, related_name='agent_outlet_extra_services')
#     commission = m.DecimalField(verbose_name=__('Комиссия'), decimal_places=1, max_digits=2)
#     is_active = m.BooleanField(__('Доступность'), default=True)
#
#     class JSONAPIMeta:
#         resource_name = 'agent-outlet-extra-services'
#
#     class Meta:
#         unique_together = ('agent_bank', 'outlet_bank', 'extra_service')
#         verbose_name = __('Настройки доп. услуг агента по торговой точке')
#         verbose_name_plural = __('Настройки доп. услуг агентов по торговым точкам')
