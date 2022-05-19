"""
Задача состоит в том чтобы добиться наиболее прямолинейного оперирования с данными
Мы пытаемся достичь этого разбивая на различные таблицы шаги создания заказа
Таким образом, фронтенд может без проблем взаимодействовать с каждым их этапов создания заявки
Мы жертвуем нормальной формой, но получаем логически проработанные этапы создания заказа
"""
from django.db import models as m
from django.utils.translation import gettext_lazy as __
from phonenumber_field.modelfields import PhoneNumberField

from apps.common.models import Model
from apps.partners.const import Country
from apps.partners.models.location import Location
from .. import const as c
from . import Order, Client


# noinspection PyUnresolvedReferences
class OrderGoodService(Model):
    """Дополнительная услуга к товарам."""
    type = m.ForeignKey(
        'misc.Accordance',
        verbose_name=__('Дополнительная услуга к товару'),
        on_delete=m.DO_NOTHING
    )
    order_good = m.ForeignKey('orders.OrderGood', on_delete=m.CASCADE, related_name='good_services')

    class JSONAPIMeta:
        resource_name = 'order-good-services'


class Credit(Model):
    """Детали кредита: первоначальный взнос и срок кредита."""
    client = m.ForeignKey(Client, on_delete=m.DO_NOTHING, related_name='credits', blank=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='credit')
    initial_payment = m.DecimalField(__('Первоначальный взнос'), max_digits=10, decimal_places=2)
    term = m.IntegerField(__('Срок'))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.client_id:
            self.client_id = self.order.client_order.client_id
        super().save(force_insert, force_update, using, update_fields)

    class JSONAPIMeta:
        resource_name = 'credits'


class Passport(Model):
    """Паспортные данные клиента."""
    # Создаётся до паспортных данные. Номер телефона предоставляется на 2 этапе
    client = m.ForeignKey(Client, on_delete=m.DO_NOTHING, related_name='passport', blank=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='passport')

    first_name = m.CharField(__('Имя'), max_length=200)
    last_name = m.CharField(__('Фамилия'), max_length=200)
    middle_name = m.CharField(__('Отчество'), max_length=200, null=True)

    birth_date = m.DateField(__('Дата рождения'))
    number = m.CharField(__('Номер'), max_length=6)
    series = m.CharField(__('Серия'), max_length=4)
    # Дату выдачи необходимо посчитать из разницы даты истечения срока действия паспорта и длительности службы паспорта
    receipt_date = m.DateField()
    division_code = m.CharField('Код подразделения', max_length=7)
    issued_by = m.CharField(__('Кем выдан'), max_length=100)  # Определяется через dadata
    sex = m.CharField(__('Пол'), choices=c.Sex.as_choices(), max_length=c.Sex.length())
    passport_main_photo = m.ImageField(null=True, upload_to='orders/passports')
    passport_registry_photo = m.ImageField(null=True, upload_to='orders/passports')
    previous_passport_photo = m.ImageField(null=True, upload_to='orders/passports')
    client_photo = m.ImageField(null=True, upload_to='orders/photos')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.client_id:
            self.client_id = self.order.client_order.client_id
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return ' '.join(n for n in (self.last_name, self.first_name, (self.middle_name or "")) if n)

    class JSONAPIMeta:
        resource_name = 'passports'


class PersonalData(Model):
    """ Этап "Персональные данные" """
    client = m.ForeignKey(Client, on_delete=m.DO_NOTHING, related_name='personal_data', blank=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='personal_data')

    registry_location = m.ForeignKey(Location, verbose_name=__('Место регистрации'),
                                     on_delete=m.DO_NOTHING, related_name='+')
    registry_date = m.DateField(__('Дата регистрации по месту регистрации'))

    habitation_location = m.ForeignKey(Location, on_delete=m.DO_NOTHING, related_name='+', null=True)
    habitation_realty_type = m.CharField(__('Тип недвижимости по адресу проживания'),
                                         choices=c.RealtyType.as_choices(), max_length=c.RealtyType.length(), null=True)
    realty_period_months = m.PositiveSmallIntegerField(__('Длительность проживания. Месяцев'))

    email = m.EmailField(__('Email'), null=True)

    birth_place = m.CharField(__('Место рождения'), max_length=200)
    birth_country = m.CharField(__('Страна рождения'), max_length=100, choices=Country.as_choices())
    # Точно не могу сказать каким образом это должно работать, лучше узнать у СФ
    life_insurance_code = m.PositiveSmallIntegerField(choices=c.LifeInsuranceCode.as_choices(), null=True)
    work_loss_insurance_code = m.PositiveSmallIntegerField(choices=c.WorkLossInsuranceCode.as_choices(), null=True)

    contact_first_name = m.CharField(__('Имя контакта'), max_length=100)
    contact_last_name = m.CharField(__('Фамилия контакта'), max_length=100)
    contact_middle_name = m.CharField(__('Отчество контакта'), max_length=100, null=True)
    contact_phone = PhoneNumberField(__('Номер телефона контакта'))
    contact_relation = m.CharField(
        __('Отношение к заемщику'),
        choices=c.ContactRelation.as_choices(),
        max_length=c.ContactRelation.length()
    )
    # noinspection PyUnresolvedReferences
    appearance = m.ForeignKey(
        'misc.Accordance',
        verbose_name=__('Внешний вид клиента'),
        on_delete=m.DO_NOTHING,
        related_name='+'
    )
    usa_citizenship = m.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.client_id:
            self.client_id = self.order.client_order.client_id
        super().save(force_insert, force_update, using, update_fields)

    class JSONAPIMeta:
        resource_name = 'personal-data'


# noinspection PyUnresolvedReferences
class FamilyData(Model):
    """ Этап "Информация о семье" """
    client = m.ForeignKey(Client, on_delete=m.DO_NOTHING, related_name='family_data', blank=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='family_data')
    marital_status = m.CharField(
        __('Семейное положение'),
        choices=c.MaritalStatus.as_choices(),
        max_length=c.MaritalStatus.length()
    )
    marriage_date = m.DateField(__('Дата вступления в брак'), null=True)
    children_count = m.PositiveSmallIntegerField(__('Количество детей'), null=True, default=0)
    dependents_count = m.PositiveSmallIntegerField(__('Количество иждивенцев'), null=True, default=0)
    partner_first_name = m.CharField('Имя супруг(а/и)', max_length=100, null=True)
    partner_last_name = m.CharField(__('Фамилия супруг(а/и)'), max_length=100, null=True)
    partner_middle_name = m.CharField(__('Отчество супруг(а/и)'), max_length=100, null=True)
    partner_is_student = m.BooleanField(default=False, null=True)
    partner_worker_status = m.CharField(__('Тип занятости'), choices=c.WorkerSocialStatus.as_choices(),
                                        max_length=c.WorkerSocialStatus.length(), null=True)
    partner_position_type = m.ForeignKey('misc.Accordance', verbose_name=__('Тип должности'),
                                         on_delete=m.DO_NOTHING,
                                         related_name='+', null=True)
    partner_retiree_status = m.CharField(__('Социальный статус пенсионера'), choices=c.RetireeSocialStatus.as_choices(),
                                         max_length=c.RetireeSocialStatus.length(), null=True)

    # TODO подумать над объединением дохода семьи / личного дохода, банкам пофиг, но мы передаём более точную информацию
    monthly_family_income = m.DecimalField(__('Среднемесячный доход семьи'), max_digits=10, decimal_places=2, null=True)
    code_word = m.CharField(__('Кодовое слово'), max_length=200)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.client_id:
            self.client_id = self.order.client_order.client_id
        super().save(force_insert, force_update, using, update_fields)

    class JSONAPIMeta:
        resource_name = 'family-data'


# noinspection PyUnresolvedReferences
class CareerEducation(Model):
    """ Этап "Образование и карьера" """
    client = m.ForeignKey(Client, on_delete=m.DO_NOTHING, related_name='career_education', blank=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='career_education')

    education = m.CharField(
        __('Образование'),
        choices=c.Education.as_choices(),
        max_length=c.Education.length()
    )
    workplace_category = m.CharField(
        __('Тип трудоустройства'),
        choices=c.WorkplaceCategory.as_choices(),
        max_length=c.WorkplaceCategory.length()
    )
    is_student = m.BooleanField(default=False)
    worker_status = m.CharField(__('Тип занятости'), choices=c.WorkerSocialStatus.as_choices(),
                                max_length=c.WorkerSocialStatus.length(), null=True)
    # noinspection PyUnresolvedReferences
    position_type = m.ForeignKey('misc.Accordance', verbose_name=__('Тип должности'), on_delete=m.DO_NOTHING,
                                 related_name='+', null=True)
    retiree_status = m.CharField(__('Социальный статус пенсионера'), choices=c.RetireeSocialStatus.as_choices(),
                                 max_length=c.RetireeSocialStatus.length(), null=True)

    # TODO объединить с доходом семьи
    monthly_income = m.DecimalField(__('Среднемесячный доход'), decimal_places=2, max_digits=10)
    monthly_expenses = m.DecimalField(__('Среднемесячные расходы'), decimal_places=2, max_digits=10)

    org_name = m.CharField(__('Название организации'), max_length=200, null=True)
    org_industry = m.ForeignKey(
        'misc.Accordance', verbose_name=__('Вид деятельности организации'), on_delete=m.DO_NOTHING,
        related_name='+', null=True
    )
    position = m.CharField(__('Должность'), max_length=200, null=True)
    org_ownership = m.ForeignKey(
        'misc.Accordance',
        verbose_name=__('Форма собственности организации'),
        on_delete=m.DO_NOTHING,
        related_name='+',
        null=True
    )  # Возможно можно как-нибудь заполнить с помощью dadata, такую инфу клиенты могут не знать
    months_of_exp = m.PositiveSmallIntegerField(__('Стаж работы в месяцах'), null=True)
    org_location = m.ForeignKey(Location, on_delete=m.DO_NOTHING, null=True)
    job_phone = m.CharField(__('Рабочий телефон'), max_length=12, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.client_id:
            self.client_id = self.order.client_order.client_id
        super().save(force_insert, force_update, using, update_fields)

    class JSONAPIMeta:
        resource_name = 'career-education'


class ExtraData(Model):
    """ Этап "Прочая информация" """
    client = m.ForeignKey(Client, on_delete=m.DO_NOTHING, related_name='extra_datas', blank=True)
    order = m.OneToOneField(Order, on_delete=m.CASCADE, related_name='extra_data')

    notification_way = m.CharField(
        __('Адрес доставки корреспонденции'),
        choices=c.NotificationWay.as_choices(),
        max_length=c.NotificationWay.length(),
        default=c.NotificationWay.REGISTRATION
    )
    previous_passport_series = m.CharField(__('Серия предыдущего паспорта'), max_length=4, null=True)
    previous_passport_number = m.CharField(__('Номер предыдущего паспорта'), max_length=6, null=True)
    previous_first_name = m.CharField(__('Предыдущее имя'), max_length=100, null=True)
    previous_last_name = m.CharField(__('Предыдущая фамилия'), max_length=100, null=True)
    previous_middle_name = m.CharField(__('Предыдущее отчество'), max_length=100, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.client_id:
            self.client_id = self.order.client_order.client_id
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f'ExtraData(id: {self.id}) client: {self.client_id} order: {self.order_id}'

    class JSONAPIMeta:
        resource_name = 'extra-data'
