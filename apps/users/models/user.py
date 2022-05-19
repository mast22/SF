from django.db import models as m
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import gettext_lazy as __
from phonenumber_field.modelfields import PhoneNumberField
from apps.common.models import Model
from apps.common.utils import compose_full_name
from ..const import Roles, UserStatus


class UserQuerySet(m.QuerySet):
    pass


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    use_in_migrations = True

    def create_superuser(self, phone, password):
        """Создание суперпользователя."""
        user = self.model(
            phone=phone, is_superuser=True,
            role=Roles.ADMIN, status=UserStatus.ACTIVE,
        )
        user.set_password(password)
        user.is_superuser = True
        user.save()
        return user


class User(Model, AbstractBaseUser):
    phone = PhoneNumberField(__('Номер телефона'), unique=True)

    first_name = m.CharField(__('Имя'), max_length=100)
    last_name = m.CharField(__('Фамилия'), max_length=100)
    middle_name = m.CharField(__('Отчество'), max_length=100, null=True)
    email = m.EmailField(__('Email'), unique=True, null=True)
    status = m.CharField(__('Статус'), choices=UserStatus.as_choices(), default=UserStatus.ACTIVE, max_length=20)
    role = m.CharField(__('Роль'), max_length=Roles.length(), choices=Roles.as_choices())
    is_superuser = m.BooleanField(__('superuser status'), default=False)
    telegram_id = m.CharField(__('ID телеграмма'), max_length=9, null=True, default=None)
    # Применимо только для агентов
    ter_man = m.ForeignKey('users.TerMan', on_delete=m.DO_NOTHING, null=True, default=None, related_name='agents')
    # Применим только для территориала
    region = m.ForeignKey('partners.Region', on_delete=m.DO_NOTHING, null=True, default=None, related_name='ter_mans')
    can_edit_bank_priority = m.BooleanField(__('Может редактировать приоритет банков'), null=True, default=None)

    USERNAME_FIELD = 'phone'
    objects = UserManager()

    class JSONAPIMeta:
        resource_name = 'users'

    class Meta:
        constraints = [
            # Аккаунт менеджеру регион задаётся на регионе через M2M.
            # Териториалу также задаётся на регионе через FK.
            m.constraints.CheckConstraint(
                name='user_region_constraint',
                check=m.Q(
                    m.Q(role=Roles.TER_MAN, region__isnull=False) |
                    m.Q(role__in=[Roles.AGENT, Roles.ADMIN, Roles.ACC_MAN], region__isnull=True)
                )
            ),
            # Поле территориал (ter_man) применимо только для агента
            m.constraints.CheckConstraint(
                name='user_ter_man_constraint',
                check=m.Q(
                    m.Q(role=Roles.AGENT, ter_man__isnull=False) |
                    m.Q(role__in=[Roles.ADMIN, Roles.ACC_MAN, Roles.TER_MAN], ter_man__isnull=True)
                )
            ),
            # Только к территориалу применимо поле возможности настройки приоритета банков
            m.constraints.CheckConstraint(
                name='user_can_edit_bank_priority_constraint',
                check=m.Q(
                    m.Q(role__in=[Roles.TER_MAN], can_edit_bank_priority__isnull=False) |
                    m.Q(role__in=[Roles.ADMIN, Roles.ACC_MAN, Roles.AGENT], can_edit_bank_priority__isnull=True)
                )
            )
        ]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.can_edit_bank_priority is None and self.role == Roles.TER_MAN:
            self.can_edit_bank_priority = False
        return super().save(force_insert, force_update, using, update_fields)

    @property
    def full_name(self) -> str:
        return compose_full_name(self.last_name, self.first_name, self.middle_name)

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def __str__(self) -> str:
        return f'{self.phone} ({self.role} {self.full_name} id:{self.id})'



class TerManManger(UserManager):
    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs).filter(role=Roles.TER_MAN)


class TerMan(User):
    """Территориальный менеджер"""
    objects = TerManManger()

    class Meta:
        proxy = True

    class JSONAPIMeta:
        resource_name = 'ter-mans'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.role = Roles.TER_MAN
        return super().save(force_insert, force_update, using, update_fields)



class AgentManager(UserManager):
    """Агент"""
    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs).filter(role=Roles.AGENT)


class Agent(User):
    objects = AgentManager()

    class Meta:
        proxy = True

    class JSONAPIMeta:
        resource_name = 'agents'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.role = Roles.AGENT
        return super().save(force_insert, force_update, using, update_fields)



class AccManManager(UserManager):
    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs).filter(role=Roles.ACC_MAN)


class AccMan(User):
    """Аккаунт-менеджен"""
    objects = AccManManager()

    class Meta:
        proxy = True

    class JSONAPIMeta:
        resource_name = 'acc-mans'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.role = Roles.ACC_MAN
        return super().save(force_insert, force_update, using, update_fields)



class AdminManager(UserManager):
    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs).filter(role=Roles.ADMIN)


class Admin(User):
    """Администратор"""
    objects = AdminManager()

    class Meta:
        proxy = True

    class JSONAPIMeta:
        resource_name = 'admins'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.role = Roles.ADMIN
        return super().save(force_insert, force_update, using, update_fields)
