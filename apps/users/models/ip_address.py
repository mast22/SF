from django.db import models as m
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as __
from netfields import InetAddressField, NetManager
from apps.common.models import Model
from .. import const as c
from .user import User


class AllowedIP(Model):
    ip = InetAddressField(__('IP-адрес'))
    user = m.ForeignKey(User, on_delete=m.CASCADE, related_name='allowed_ips')
    is_active = m.BooleanField(__('Активен'), default=True)

    def clean(self):
        if self.user.role not in c.ROLES_BY_IP:
            raise ValidationError(f'Нельзя создать разрешённый IP-адрес для пользователя с ролью {self.user.role}')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class JSONAPIMeta:
        resource_name = 'allowed-ips'

    # objects = NetManager()
    class Meta:
        verbose_name = __('Разрешённый IP-адрес')
        verbose_name_plural = __('Разрешённые IP-адреса')
        unique_together = ('ip', 'user',)
