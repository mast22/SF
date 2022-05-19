from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models as m
from django.conf import settings
from django.utils.translation import gettext_lazy as __
from apps.common.models import Model
from apps.banks.models import CreditProduct, ExtraService
from apps.banks.priority import set_order_credit_prioriy
from apps.banks.commission import (get_agent_credit_product_commission, get_agent_extra_service_commission,
    get_terman_credit_product_commission, get_terman_extra_service_commission)
from apps.banks.const import BankPriorityChoice
from .. import const as c
from .order import Order
from ...common.transitions import change_state


class OrderCreditProduct(Model):
    """ Банковские продукты в заказе
    Выступает в качестве "отправки" заявки в банк по кредитному продукту
    """
    credit_product = m.ForeignKey(CreditProduct, on_delete=m.CASCADE, related_name='order_credit_products')
    extra_services = m.ManyToManyField(ExtraService, through='OrderExtraService')
    order = m.ForeignKey(Order, on_delete=m.CASCADE, related_name='order_credit_products')
    status = m.CharField(
        __('Статус согласования кредита'),
        choices=c.CreditProductStatus.as_choices(),
        default=c.CreditProductStatus.NOT_SENT,
        max_length=c.CreditProductStatus.length(),
    )
    agent_commission = m.DecimalField(__('Комиссия агента'), max_digits=12, decimal_places=2,
            default=Decimal(0))
    terman_commission = m.DecimalField(__('Комиссия территориала'), max_digits=12, decimal_places=2,
            default=Decimal(0))
    priority = m.PositiveSmallIntegerField(__('Приоритет банка'),
                choices=BankPriorityChoice.as_choices(), default=BankPriorityChoice.FIRST)
    bank_id = m.CharField(__('ID заказа в банке'), max_length=200, null=True)
    # В случае провалившегося скоринга вписываем причину отказа
    bank_data = m.CharField(__('Ответ банка'), null=True, max_length=1000) # Ответ от банка
    required_fields = m.TextField(__('Недостающие поля'), null=True) # Может содержаться в ответе от банка
    explanation = m.CharField(__('Пояснение к ответу банка'), null=True, max_length=1000) # Пояснение к ответу банка от разработчика
    last_modified = m.DateTimeField(auto_now=True)
    created_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.id} CP:{self.credit_product_id}, Order:{self.order_id} status:{self.status}'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None:
            # Валидация не должна срабатывать при обновлении
            self.validate_unique()
        if not self.priority:
            self.priority = set_order_credit_prioriy(self)
        if not self.agent_commission and settings.CALCULATE_OPERATIONAL_DATA:
            self.agent_commission = get_agent_credit_product_commission(self.order, self.credit_product)
        if not self.terman_commission:
            self.terman_commission = get_terman_credit_product_commission(self.order, self.credit_product)
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def validate_unique(self, *args, **kwargs):
        """ Невозможно создать UniqueConstraint на объекты с отношением
        Необходимо проверить, что не существует другой отправки (OCP) с таким же банком
        """
        super(OrderCreditProduct, self).validate_unique(*args, **kwargs)

        ocps_with_same_bank = OrderCreditProduct.objects.filter(
            credit_product__bank=self.credit_product.bank,
            order=self.order,
        ).exists()
        if ocps_with_same_bank:
            raise ValidationError(message='Должна быть только одна отправка (OCP) на каждый банк')

    class JSONAPIMeta:
        resource_name = 'order-credit-products'

    def update_with_status(self, new_status: str, bank_data=None, required_fields: str=None, save: bool=True):
        """ Обновляет статус отправки если необходимо
        Каждое изменение статуса может повлиять на статус заказа в целом """
        assert new_status in c.CreditProductStatus.keys(), "Статус должен быть один из списка статусов отправки заказа"

        self.status = new_status
        if bank_data is not None:
            self.bank_data = bank_data
        if required_fields is not None:
            self.required_fields = required_fields
        if save:
            self.save(update_fields=['bank_data', 'status'])

        # Проверка того, что заказ был отклонен всеми банками
        if self.order.status in [c.OrderStatus.SCORING, c.OrderStatus.SELECTION]:
            # Находим количество результатов скоринга (isnull), которые прошли с неудачей
            ocps_exists = self.order.order_credit_products.filter(
                # Найдет те, которые закончились без ошибок
                ~m.Q(status__in=(c.CreditProductStatus.REJECTED, c.CreditProductStatus.TECHNICAL_ERROR)) |
                # Найдет те, которые закончились
                m.Q(bank_id__isnull=False)
            ).exists()
            # Только в случае если не найдет те, которые не прошли скоринг и те, которые прошли успешно
            # Мы сможем сказать что заказ отклонен всеми банками
            if not ocps_exists:
                self.order.status = c.OrderStatus.REJECTED
                self.order.save(update_fields=('status',))

        # Если нам по OCP пришел положительный результат от банка, то мы можем перевести заказ в статуса выбора
        # Кредитного продукта, но он уже не должен быть в статусе выбора
        if new_status == c.CreditProductStatus.SUCCESS and self.order.status != c.OrderStatus.SELECTION:
            change_state(self.order.set_selection, 'Невозможно установить статус заказа на выбор кредитного продукта')
            self.order.save()


class OrderExtraService(Model):
    """ Выбранные доп. услуги в заявке"""
    extra_service = m.ForeignKey(ExtraService, on_delete=m.CASCADE, related_name='order_extra_services')
    order_credit_product = m.ForeignKey(OrderCreditProduct, on_delete=m.CASCADE, related_name='order_extra_services')
    agent_commission = m.DecimalField(__('Комиссия агента'), max_digits=12, decimal_places=2,
            default=Decimal(0))
    terman_commission = m.DecimalField(__('Комиссия территориала'), max_digits=12, decimal_places=2,
            default=Decimal(0))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.id or force_update or update_fields:
            raise AttributeError(f'OrderExtraService {self} cant be updated')
        if not self.agent_commission:
            self.agent_commission = get_agent_extra_service_commission(
                    self.order_credit_product.order, self.extra_service
            )
        if not self.terman_commission:
            self.terman_commission = get_terman_extra_service_commission(
                self.order_credit_product.order, self.extra_service
            )
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'{self.pk} with {self.extra_service} for {self.order_credit_product}.' \
               f' Commission: {self.agent_commission}'

    class JSONAPIMeta:
        resource_name = 'order-extra-services'
