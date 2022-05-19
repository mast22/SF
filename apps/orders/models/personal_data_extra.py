from django.db import models as m
from django.utils.translation import gettext_lazy as __
from apps.common.models import Model, BaseTokenModel
from .order_flow import PersonalData
from .. import const as c


class PersonalDataTempToken(BaseTokenModel):
    personal_data = m.ForeignKey(PersonalData, on_delete=m.CASCADE)

    class Meta:
        verbose_name= __('Временный токен для загрузки сканов паспорта')
        verbose_name_plural = __('Временные токены для загрузки сканов паспорта')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.key:
            self.key = self.generate_key(c.PERSONAL_DATA_TEMP_TOKEN_LENGTH)
        return super().save(force_insert, force_update, using, update_fields)


class PersonalDataFile(Model):
    personal_data = m.ForeignKey(PersonalData, on_delete=m.CASCADE)
    page = m.PositiveIntegerField(__('Страница'), default=1)
    image = m.ImageField(__('Скан страницы'), upload_to='', storage=None)
    is_recognized = m.BooleanField(__('Распознано'), default=False)

    class Meta:
        verbose_name = __('Скан паспорта')
        verbose_name_plural = __('Сканы паспорта')

