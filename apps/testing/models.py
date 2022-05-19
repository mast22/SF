from django.db import models as m
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.utils import generate_random_uuid
from apps.msgs.const import SendStatus, MessageType, MessageSource


class DummyMessage(m.Model):
    subject = m.CharField(_('Заголовок'), max_length=1000, default='', blank=True)
    message = m.TextField(_('Текст'), default='', blank=True)

    sender = m.CharField(_('Отправитель'), max_length=1000, null=True, blank=True)
    receiver = m.CharField(_('Получатель'), max_length=1000, null=True, blank=True)
    data = m.JSONField(_('Сырые данные'), null=True, blank=True)

    source = m.CharField(_('Тип отправки'), choices=MessageSource.as_choices(),
            default=MessageSource.NOTIFICATION, max_length=20)
    type = m.CharField(_('Тип сообщения'), choices=MessageType.as_choices(), default=MessageType.SMS, max_length=20)
    status = m.CharField(_('Status'), choices=SendStatus.as_choices(), default=SendStatus.SENT, max_length=20)
    uuid = m.CharField(_('UUID'), max_length=200, null=True, blank=True)

    sent_at = m.DateTimeField(_('Дата отправки'), auto_now_add=True)
    received_at = m.DateTimeField(_('Дата получения'), null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.uuid:
            self.uuid = generate_random_uuid()
        if self.receiver and not self.received_at:
            self.received_at = timezone.now()
        return super().save(force_insert=force_insert, force_update=force_update,
                            using=using, update_fields=update_fields)

    def __str__(self):
        return f'DummyMessage from {self.sender} to {self.receiver}. ' \
               f'Subj: {self.subject} type: {self.type} message: {self.message} data: {self.data}'

    class JSONAPIMeta:
        resource_name = 'testing-dummy-messages'
