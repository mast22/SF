from django.db import models as m
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as __
from apps.common.models import BaseTokenModel
from .. import const as c


class OrderTempToken(BaseTokenModel):
    """Временный токен для ссылки в qr-коде"""
    order = m.ForeignKey('orders.Order', on_delete=m.CASCADE)
    type = m.CharField(__('Тип временного токена'), choices=c.OrderTempTokenType.as_choices(),
            max_length=c.OrderTempTokenType.length())

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.key:
            self.key = self.generate_key(128)
        if not self.moment_end:
            cur_moment = self.created_at if self.created_at else tz.now()
            self.moment_end = cur_moment + tz.timedelta(seconds=c.ORDER_TEMP_TOKEN_EXPIRES_TIMEDELTA)
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f'OrderTempToken {self.key} for order: {self.order}'
