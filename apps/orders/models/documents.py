from django.db import models as m
from django.utils.translation import gettext_lazy as __

from apps.common.models import Model
from .. import const as c
from . import Order


class Contract(Model):
    """Договор."""
    created_at = m.DateTimeField(__('Дата добавления'), auto_now_add=True)
    changed_at = m.DateTimeField(__('Дата изменения'), auto_now=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='contract')
    # noinspection PyUnresolvedReferences
    delivery = m.ForeignKey('deliveries.Delivery', on_delete=m.SET_NULL, null=True, related_name='contracts')
    status = m.CharField(__('Статус'), choices=c.ContractStatus.as_choices(), default=c.ContractStatus.OUTLET,
        max_length=c.ContractStatus.length())
    bank_number = m.CharField(__('Номер договора'), max_length=200, null=True)
    bank_authorization_code = m.CharField(__('Код авторизации в банке'), max_length=200, null=True)
    bank_credit_amount = m.DecimalField(__('Сумма кредита в банке'), decimal_places=2, max_digits=10, null=True)
    bank_goods_price = m.DecimalField(__('Цена товаров в банке'), decimal_places=2, max_digits=10, null=True)

    class JSONAPIMeta:
        resource_name = 'contracts'


class DocumentToSign(Model):
    """Отсканированный документ"""
    order = m.ForeignKey(Order, on_delete=m.CASCADE, related_name='documents_to_sign')
    file = m.FileField(__('Файл'), upload_to='orders/documents_to_sign')
    file_name = m.CharField(__('Название файла'), max_length=200, default='unknown')
    file_type = m.CharField(__('Логический тип файла'), max_length=100, default='unknown')
    file_ext = m.CharField(__('Расширение'), max_length=10, null=True)

    class JSONAPIMeta:
        resource_name = 'documents-to-sign'


class DocumentSigned(Model):
    """Подписанный документ"""
    order = m.ForeignKey(Order, on_delete=m.CASCADE, related_name='documents_signed')
    file = m.FileField(__('Файл'), upload_to='orders/documents_signed')
    file_ext = m.CharField(__('Расширение'), max_length=10, null=True)

    class JSONAPIMeta:
        resource_name = 'documents-signed'
