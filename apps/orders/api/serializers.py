from datetime import date, datetime
from functools import reduce

from dateutil.relativedelta import relativedelta

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import exceptions as rest_exc
from rest_framework.serializers import Serializer, ModelSerializer, CharField, DateTimeField
from rest_framework_json_api import serializers as s

import apps.deliveries
import apps.deliveries.models
from apps.banks.models import CreditProduct, ExtraService
from apps.banks.api.serializers import CreditProductSerializer, ExtraServiceSerializer
from apps.common.serializer_fields import ImageField
from apps.misc.api.serializers import AccordanceSerializer
from apps.partners import models as partners_models
from apps.partners.api.serializers import LocationSerializer, PartnerSerializer
from apps.users.api.serializers import AgentIncludedSerializer
from apps.users.const import TempTokenType
from apps.users.models import TempToken
from apps.common.utils import get_person_age, xor
from .validators import check_forbidden_words
from .. import const as c
from .. import models as m
from ..const import MaritalStatus, WorkplaceCategory


class PersonalDataSerializer(s.ModelSerializer):
    full_name = s.CharField(read_only=True)
    included_serializers = {
        'habitation_location': LocationSerializer,
        'position_type': AccordanceSerializer,
        'registry_location': LocationSerializer,
    }

    class Meta:
        model = m.PersonalData
        fields = '__all__'
        meta_fields = ['full_name']

    def validate_registry_date(self, registry_date: date):
        """ Валидация даты регистрации пользователя """
        now = date.today()

        if registry_date > now:
            raise s.ValidationError('Дата регистрации не может быть больше текущего дня')

        return registry_date

    def validate_contact_first_name(self, value: str):
        check_forbidden_words(value)

        return value

    def validate_contact_last_name(self, value: str):
        check_forbidden_words(value)

        return value

    def validate_contact_middle_name(self, value: str):
        if value is not None:
            check_forbidden_words(value)

        return value


class FamilyDataSerializer(s.ModelSerializer):
    included_serializers = {
        'partner_position_type': AccordanceSerializer
    }

    class Meta:
        model = m.FamilyData
        fields = '__all__'

    def validate(self, payload: dict):
        partner_worker_status = payload.get('partner_worker_status', None)
        partner_position_type = payload.get('partner_position_type', None)
        marital_status = payload.get('marital_status', None)

        corresponding_field_values_presence = [
            bool(payload.get('marriage_date', None)),
            bool(payload.get('partner_first_name', None)),
            bool(payload.get('partner_last_name', None)),
            bool(payload.get('partner_middle_name', None)),
        ]
        status_mark_presence = [
            bool(payload.get('partner_retiree_status', None)),
            bool(payload.get('partner_is_student', None)),
            bool(partner_worker_status),
        ]

        if marital_status != MaritalStatus.MARRIED:
            if any(corresponding_field_values_presence):
                raise s.ValidationError('Информация о супруге не может быть задана для клиента без супруга')

        if marital_status == MaritalStatus.MARRIED:
            if not all(corresponding_field_values_presence):
                raise s.ValidationError('Информация о супруге должна быть задана для клиента с супругой')

            if len(list(filter(lambda x: x, status_mark_presence))) != 1:
                raise s.ValidationError('Только одно значение из социальных статусов должно быть указано')

            if partner_worker_status or partner_position_type:
                if xor(partner_worker_status, partner_position_type):
                    raise s.ValidationError('Cтатус работника и тип должности должны быть указаны вместе')

        return payload

    def validate_code_word(self, value: str):
        check_forbidden_words(value)

        return value


class OrderOutletSerializer(s.ModelSerializer):
    included_serializers = {
        'partner': PartnerSerializer,
        'address': LocationSerializer,
    }

    class Meta:
        model = partners_models.Outlet
        fields = ['id', 'name', 'phone', 'email', 'is_active', 'telegram_id', 'partner', 'address', ]


class GoodSerializer(s.ModelSerializer):
    class Meta:
        model = m.Good
        fields = '__all__'


class OrderGoodSerializer(s.ModelSerializer):
    included_serializers = {
        'good': GoodSerializer
    }

    class Meta:
        model = m.OrderGood
        fields = '__all__'


class OrderGoodServiceSerializer(s.ModelSerializer):
    class Meta:
        model = m.OrderGoodService
        fields = '__all__'


class OrderHistorySerializer(s.ModelSerializer):
    class Meta:
        model = m.OrderHistory
        fields = '__all__'


class OrderCreditProductSerializer(s.ModelSerializer):
    extra_services = s.ResourceRelatedField(queryset=ExtraService.objects.all(), many=True, required=False)
    order_extra_services = s.ResourceRelatedField(read_only=True, many=True, required=False)

    included_serializers = {
        'order': 'apps.orders.api.serializers.OrderIncludeSerializer',
        'credit_product': CreditProductSerializer,
        'extra_services': ExtraServiceSerializer,
        'order_extra_services': 'apps.orders.api.serializers.OrderExtraServiceSerializer'
    }

    class Meta:
        model = m.OrderCreditProduct
        fields = (
            'id', 'order', 'credit_product', 'status',
            'agent_commission', 'priority',
            'bank_id', 'bank_data',
            'last_modified', 'created_at',
            'extra_services', 'order_extra_services',
        )


class OrderExtraServiceSerializer(s.ModelSerializer):
    agent_commission = s.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    included_serializers = {
        'order_credit_product': OrderCreditProductSerializer,
        'extra_service': ExtraServiceSerializer,
    }

    class Meta:
        model = m.OrderExtraService
        fields = '__all__'


class PassportSerializer(s.ModelSerializer):
    class Meta:
        model = m.Passport
        fields = '__all__'

    def validate_birth_date(self, value: date):
        now = date.today()
        age = get_person_age(value, now)
        if age < 18:
            raise s.ValidationError('Клиент должен быть старше 18 лет')

        if age > 100:
            raise s.ValidationError('Клиент должен быть младше 100 лет')

        return value

    @staticmethod
    def proceed_passport_date_validation(receipt_date: datetime, birth_date: datetime, years_offset: int):
        birth_date_passport_received_date = birth_date + relativedelta(years=years_offset)
        if birth_date_passport_received_date > receipt_date: raise s.ValidationError(
            'Даты рождения пользователя не совпадает с датой выдачи паспорта'
        )

    def validate(self, passport: dict):
        """ Алгоритм проверки валидности даты паспорта
        Если существует некоторый промежуток времени между днем рождения в 14, 20, 45 лет и выдачей паспорта
        То дата валидна
        """
        today = date.today()
        birth_date = passport['birth_date']
        receipt_date = passport['receipt_date']
        age = get_person_age(birth_date, today)

        if 14 <= age < 20:
            self.proceed_passport_date_validation(receipt_date, birth_date, 14)
        elif 20 <= age < 45:
            self.proceed_passport_date_validation(receipt_date, birth_date, 20)
        elif age >= 45:
            self.proceed_passport_date_validation(receipt_date, birth_date, 45)

        return passport

    def validate_first_name(self, value: str):
        check_forbidden_words(value)

        return value

    def validate_last_name(self, value: str):
        check_forbidden_words(value)

        return value

    def validate_middle_name(self, value: str):
        check_forbidden_words(value)

        return value

    def validate_series(self, value: str):
        if not value.isdigit() or len(value) != 4:
            raise s.ValidationError('Длина серии паспорта должна быть строго 4 символа и состоять из цифр')

        return value

    def validate_number(self, value: str):
        if not value.isdigit() or len(value) != 6:
            raise s.ValidationError('Длина номера паспорта должна быть строго 4 символа и состоять из цифр')

        return value

class ClientSerializer(s.ModelSerializer):
    phone = PhoneNumberField(required=True)
    included_serializers = {
        'personal_data': PersonalDataSerializer,
        'passport': PassportSerializer,
    }

    class Meta:
        model = m.Client
        fields = ['id', 'phone', 'personal_data', 'passport']
        read_only_fields = ('personal_data', 'passport',)


class ClientSendCodeSerializer(Serializer):
    phone = PhoneNumberField(required=True)

    def validate(self, attrs):
        # 2. Проверить, нет ли на данного юзера уже записей в temp_token,
        # с repeat_at больше текущего времени
        try:
            TempToken.get_count(phone=attrs['phone'])
        except TempToken.TokenLimitException:
            raise rest_exc.Throttled(code='too_often', detail='Слишком много запросов, попробуйте позже')

        return attrs


class ClientCheckCodeSerializer(Serializer):
    temp_token = s.CharField(required=True, min_length=64, max_length=128)
    code = s.CharField(required=True, min_length=4, max_length=8)

    def validate(self, attrs):
        # 1. Вытаскиваю temp_token:
        try:
            temp_token = TempToken.objects.get_token(attrs['temp_token'], TempTokenType.NEW_CLIENT)
        except (TempToken.DoesNotExist, TempToken.TokenIsOutdatedException):
            raise rest_exc.ValidationError(code='wrong_temp_token', detail='Не верный временный token! Харам!')

        attrs['temp_token'] = temp_token
        return attrs


class ClientSendCodeRespSerializer(Serializer):
    detail = s.CharField()
    temp_token = s.CharField()
    expires = s.DateTimeField()
    repeat = s.DateTimeField()
    now = s.DateTimeField(help_text='Текущее время сервера')


class CareerEducationSerializer(s.ModelSerializer):
    included_serializers = {
        'org_industry': AccordanceSerializer,
        'org_location': LocationSerializer,
    }

    class Meta:
        model = m.CareerEducation
        fields = '__all__'

    def validate(self, payload):
        corresponding_field_values_presence = [
            bool(payload.get('org_name', None)),
            bool(payload.get('org_industry', None)),
            bool(payload.get('position', None)),
            bool(payload.get('org_ownership', None)),
            bool(payload.get('org_location', None)),
            bool(payload.get('job_phone', None)),
        ]
        possible_statuses_field_values = [
            bool(payload.get('is_student', None)),
            bool(payload.get('worker_status', None)),
            bool(payload.get('retiree_status', None)),
        ]

        if payload['workplace_category'] == WorkplaceCategory.UNEMPLOYED:
            if reduce(lambda x, y: x or y, corresponding_field_values_presence):
                raise s.ValidationError('Информация о работе не может быть задана для безработного клиента')

        if payload['workplace_category'] != WorkplaceCategory.UNEMPLOYED:
            if not reduce(lambda x, y: x and y, corresponding_field_values_presence):
                raise s.ValidationError('Информация о работе должна быть задана для работающего клиента')

        if len(list(filter(lambda x: x, possible_statuses_field_values))) != 1:
            raise s.ValidationError('Одно значение из трех социальных статусов должно быть указано')

        return payload


class CreditSerializer(s.ModelSerializer):
    order = s.ResourceRelatedField(queryset=m.Order.objects.all(), required=False)

    class Meta:
        model = m.Credit
        fields = '__all__'


class ClientOrderSerializer(s.ModelSerializer):
    phone = PhoneNumberField(required=False)

    class Meta:
        model = m.ClientOrder
        fields = '__all__'


class ExtraDataSerializer(s.ModelSerializer):
    class Meta:
        model = m.ExtraData
        fields = '__all__'

    def validate_previous_first_name(self, value: str):
        if value is not None:
            check_forbidden_words(value)

        return value

    def validate_previous_last_name(self, value: str):
        if value is not None:
            check_forbidden_words(value)

        return value

    def validate_previous_middle_name(self, value: str):
        if value is not None:
            check_forbidden_words(value)

        return value

    def previous_passport_series(self, value: str):
        if value is not None:
            if not value.isdigit() or len(value) != 4:
                raise s.ValidationError('Длина серии паспорта должна быть строго 4 символа и состоять из цифр')

        return value

    def previous_passport_number(self, value: str):
        if value is not None:
            if not value.isdigit() or len(value) != 6:
                raise s.ValidationError('Длина номера паспорта должна быть строго 4 символа и состоять из цифр')

        return value


class OrderSerializer(s.ModelSerializer):
    """
    client_full_name - personal_data.full_name
    contract_number - contract.number
    """
    purchase_amount = s.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    agent_commission = s.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    credit_products = s.ResourceRelatedField(queryset=CreditProduct.objects.all(), many=True, required=False)
    order_credit_products = s.ResourceRelatedField(
        queryset=m.OrderCreditProduct.objects.all(), many=True, required=False
    )

    history = s.ResourceRelatedField(
        # queryset=order_models.OrderStatusHistory.objects.all().order_by('-changed_at')[:20],
        read_only=True, many=True,
    )

    included_serializers = {
        'personal_data': PersonalDataSerializer,
        'agent': AgentIncludedSerializer,
        'outlet': OrderOutletSerializer,
        'goods': OrderGoodSerializer,
        'history': OrderHistorySerializer,
        'order_credit_products': OrderCreditProductSerializer,
        'chosen_product': CreditProductSerializer,
        'family_data': FamilyDataSerializer,
        'passport': PassportSerializer,
        'client_order': ClientOrderSerializer,
        'career_education': CareerEducationSerializer,
        'credit': CreditSerializer,
        'extra_data': ExtraDataSerializer,
        'credit_products': CreditProductSerializer,
    }

    class Meta:
        model = m.Order
        fields = (
            'id', 'agent', 'outlet', 'status', 'client_order', 'goods',
            'credit', 'family_data', 'personal_data',
            'passport', 'career_education', 'extra_data',
            'created_at', 'changed_at', 'telegram_order',
            'chosen_product', 'credit_products', 'order_credit_products',
            'purchase_amount', 'agent_commission', 'history',
        )
        read_only_fields = (
            'agent_commission', 'history', 'goods',
            'credit', 'family_data', 'personal_data',
            'passport', 'career_education', 'extra_data',
            'created_at', 'changed_at', 'telegram_order',
        )

    class JSONAPIMeta:
        included_resources = []


class UpdateOrderSerializer(OrderSerializer):
    """ Изменения некоторый полей запрещено для сохранения валидности данных """
    class Meta(OrderSerializer.Meta):
        read_only_fields = OrderSerializer.Meta.read_only_fields + ('outlet', 'agent', 'client_order')


class XLSXOrderSerializer(ModelSerializer):
    purchase_amount = s.DecimalField(decimal_places=2, max_digits=10)
    initial_payment = s.IntegerField(source='credit.initial_payment')
    term = s.IntegerField(source='credit.term')
    outlet = s.CharField(source='outlet.name')
    outlet_address = s.SerializerMethodField()
    loan_amount = s.SerializerMethodField()
    client_full_name = s.SerializerMethodField()
    bank = s.SerializerMethodField()
    status = s.SerializerMethodField()
    agent = s.SerializerMethodField()
    created_at = s.SerializerMethodField()

    def get_created_at(self, order):
        return order.created_at.strftime("\'%Y-%m-%d %X")

    def get_bank(self, order):
        if order.chosen_product is None:
            return None
        return order.chosen_product.bank.get_name_display()

    def get_loan_amount(self, order):
        return order.purchase_amount - order.credit.initial_payment

    def get_outlet_address(self, order):
        return order.outlet.address.to_human()

    def get_status(self, order):
        return order.get_status_display()

    def get_agent(self, order):
        return order.agent.full_name

    def get_client_full_name(self, order):
        return order.passport.full_name

    class Meta(OrderSerializer.Meta):
        fields = list(c.order_xlsx_fields.keys())
        model = m.Order


class OrderIncludeSerializer(s.ModelSerializer):
    """
    client_full_name - personal_data.full_name
    contract_number - contract.number
    """
    # total = s.SerializerMethodField()
    included_serializers = {
        'agent': AgentIncludedSerializer,
        'outlet': OrderOutletSerializer,
        'passport': PassportSerializer,
        'client_order': ClientOrderSerializer,
    }

    class Meta:
        model = m.Order
        fields = (
            'id', 'status',
            'created_at', 'changed_at',
            'purchase_amount',
            'agent', 'outlet', 'passport', 'client_order',
        )
        read_only_fields = (
            'purchase_amount',
        )


class DeliverySerializer(s.ModelSerializer):
    class Meta:
        model = apps.deliveries.models.Delivery


class GetOrderStatusSerializer(ModelSerializer):
    class Meta:
        model = m.Order
        fields = ('status', 'changed_at')


class ChooseCreditProductSerializer(ModelSerializer):
    chosen_product = s.PrimaryKeyRelatedField(queryset=m.OrderCreditProduct.objects.all())

    class Meta:
        model = m.Order
        fields = ('chosen_product',)


class OrderSendDocumentsSeriazlier(Serializer):
    contract = s.ResourceRelatedField(queryset=m.Contract.objects.all(), required=False)

    class Meta:
        model = m.Order
        fields = ('contract',)


class OrderSendToScoringSerializer(Serializer):
    pass


class OrderSendToAuthorizationSerializer(Serializer):
    pass


class CreateTelegramOrderSerializer(Serializer):
    passport_main_photo = ImageField()
    passport_registry_photo = ImageField()
    previous_passport_photo = ImageField()
    client_photo = ImageField()
    api_id = CharField()
    phone = PhoneNumberField()
    created_at = DateTimeField()


class TelegramOrderSerializer(ModelSerializer):
    class Meta:
        model = m.TelegramOrder
        fields = '__all__'


class UploadPassportPhotosSerializer(Serializer):
    passport_main_photo = ImageField()
    passport_registry_photo = ImageField()
    previous_passport_photo = ImageField(required=False)
    client_photo = ImageField()


class OrderTempTokenSerializer(ModelSerializer):
    url = s.SerializerMethodField()

    def get_url(self, temp_token):
        local_url = c.OrderTempTokenType.plural(temp_token.type).format(key=temp_token.key)
        absolute_url = self.context['request'].build_absolute_uri(local_url)
        return absolute_url

    class Meta:
        model = m.OrderTempToken
        fields = ('url',)


class ContractSerializer(s.ModelSerializer):
    included_serializers = {
        'order': OrderIncludeSerializer,
    }
    hello = s.SerializerMethodField()

    def get_hello(self, contract):
        return '123'

    class Meta:
        model = m.Contract
        fields = '__all__'
        meta_fields = ['hello']


class ContractStatusSerializer(s.ModelSerializer):
    class Meta:
        model = m.Contract
        fields = ('status',)


class DocumentToSignSerializer(s.ModelSerializer):
    class Meta:
        model = m.DocumentToSign
        fields = ('id', 'order', 'file', 'file_ext')


class DocumentSignedSerializer(s.ModelSerializer):
    class Meta:
        model = m.DocumentSigned
        fields = ('id', 'order', 'file', 'file_ext')
