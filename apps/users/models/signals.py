from django.db.models.signals import pre_save, post_save, pre_delete, post_delete, m2m_changed
from django.dispatch import receiver

from apps.msgs.shortcuts import send_notification
from apps.common.utils import generate_random_token
from .user import User
from .. import const as c



@receiver(signal=pre_save, sender=User)
def notification_on_ter_man_status_changed(sender, instance: User, created, *args, **kwargs):
    # Territorial Manager. On add, on block, on remove. Send to all admins.
    if instance and instance.role == c.Roles.TER_MAN:

        msg_type_to_send = None

        if created and instance.status == c.UserStatus.ACTIVE:
            # New ter.manager was created:
            msg_type_to_send = 'ter_man_created'
        elif instance.status != c.UserStatus.ACTIVE:
            user_pre_save = User.objects.only('id', 'status').get(instance.id)
            if instance.status != user_pre_save.status:
                if instance.status == c.UserStatus.BLOCKED:
                    # Ter.manager was blocked
                    msg_type_to_send = 'ter_man_blocked'
                elif instance.status == c.UserStatus.REMOVED:
                    # Ter.manager was removed
                    msg_type_to_send = 'ter_man_removed'

        if msg_type_to_send:
            receivers = User.objects.filter(role=c.Roles.ADMIN)
            for rec in receivers:
                send_notification(rec, msg_type_to_send, {})


@receiver(signal=post_save, sender=User)
def notification_with_new_password(sender, instance: User, created, *args, **kwargs):
    if created:
        user = instance
        if user.password is None:
            passwd = generate_random_token(10)
            user.set_password(passwd)
            user.save()
            send_notification(user, 'password_generated', {'password': passwd})




