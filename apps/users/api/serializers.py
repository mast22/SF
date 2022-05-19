from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as __
from rest_framework_json_api import serializers as s
from rest_framework import serializers as rs
from rest_framework.exceptions import ValidationError
from apps.banks.models import AgentBank
from apps.partners.models import Region
from .. import models as m


class BaseUserSerializer(s.ModelSerializer):
    password = s.CharField(write_only=True,
        help_text='Leave empty if no change needed',
        style={'input_type': 'password', 'placeholder': 'Password'}
    )

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user


class TerManIncludedSerializer(s.ModelSerializer):
    full_name = s.CharField(read_only=True)

    class Meta:
        model = m.TerMan
        fields = (
            'id', 'phone', 'email', 'status', 'role', 'region', 'full_name',
        )


class UserSerializer(BaseUserSerializer):
    full_name = s.CharField(read_only=True)

    agent_banks = s.ResourceRelatedField(
        queryset=AgentBank.objects,
        many=True,
        required=False,
    )
    managed_regions = s.ResourceRelatedField(
        queryset=Region.objects,
        many=True,
        required=False,
    )
    included_serializers = {
        'region': 'apps.partners.api.serializers.RegionSerializer',
        'ter_man': TerManIncludedSerializer,
        'agent_banks': 'apps.banks.api.serializers.AgentBankSerializer',
        'managed_regions': 'apps.partners.api.serializers.RegionSerializer',
    }

    class Meta:
        model = m.User
        fields = '__all__'
        read_only_fields = ('last_login',)
        meta_fields = ('full_name',)



class UserListSerializer(rs.ModelSerializer):
    class Meta:
        model = m.User
        exclude = ('last_login', 'password',)


class ChangePasswordSerializer(s.Serializer):
    old_password = s.CharField(validators=[validate_password], write_only=True, required=True)
    new_password = s.CharField(validators=[validate_password], write_only=True, required=True)

    def validate(self, attrs):
        user = self.instance
        if not user or not user.check_password(attrs['old_password']):
            raise ValidationError('Текущий пароль пользователя не корректный')
        return attrs


class AgentSerializer(BaseUserSerializer):
    full_name = s.CharField(read_only=True)
    agent_banks = s.ResourceRelatedField(
        queryset=AgentBank.objects,
        many=True,
        required=False,
    )
    included_serializers = {
        'ter_man': TerManIncludedSerializer,
        'agent_banks': 'apps.banks.api.serializers.AgentBankSerializer',
    }

    class Meta:
        model = m.Agent
        exclude = ('region', 'can_edit_bank_priority', 'is_superuser')
        read_only_fields = ('role', 'last_login',)
        meta_fields = ('full_name',)


class AgentIncludedSerializer(s.ModelSerializer):
    full_name = s.CharField(read_only=True)
    region = s.ResourceRelatedField(
        queryset=Region.objects,
        many=False,
    )
    included_serializers = {
        'region': 'apps.partners.api.serializers.RegionSerializer',
    }

    class Meta:
        model = m.Agent
        exclude = ('last_login', 'password',)
        meta_fields = ('full_name',)



class TerManSerializer(BaseUserSerializer):
    full_name = s.CharField(read_only=True)
    region = s.ResourceRelatedField(queryset=Region.objects, required=True, label=__('Регион'))
    included_serializers = {
        'region': 'apps.partners.api.serializers.RegionSerializer',
    }

    class Meta:
        model = m.TerMan
        fields = (
            'id', 'phone', 'first_name', 'last_name', 'middle_name',
            'email', 'status', 'password', 'role', 'telegram_id', 'region', 'can_edit_bank_priority',
        )
        read_only_fields = ('role', 'last_login',)
        meta_fields = ('full_name',)


class AccManSerializer(BaseUserSerializer):
    full_name = s.CharField(read_only=True)
    managed_regions = s.ResourceRelatedField(
        queryset=Region.objects,
        many=True,
        required=False,
    )
    included_serializers = {
        'managed_regions': 'apps.partners.api.serializers.RegionSerializer',
        'allowed_ips': 'apps.users.api.serializers.AllowedIPSerializer',
    }

    class Meta:
        model = m.AccMan
        exclude = ('region', 'can_edit_bank_priority', 'is_superuser', 'ter_man')
        read_only_fields = ('role', 'last_login',)
        meta_fields = ('full_name',)


class AllowedIPSerializer(s.ModelSerializer):
    included_serializers = {
        'user': UserSerializer,
    }

    class Meta:
        model = m.AllowedIP
        fields = ['user', 'ip', 'is_active']


from apps.banks.api.serializers import CreditProductSerializer, ExtraServiceSerializer, BankSerializer


class CommissionReportSummarySerializer(s.Serializer):
    bank = BankSerializer()
    commission_min = s.DecimalField(decimal_places=2, max_digits=12)
    commission_max = s.DecimalField(decimal_places=2, max_digits=12)
    sum_cur_month = s.DecimalField(decimal_places=2, max_digits=12)
    sum_period = s.DecimalField(decimal_places=2, max_digits=12)
    sum_all = s.DecimalField(decimal_places=2, max_digits=12)

    class Meta:
        resource_name = 'CommissionReportSummary'


class CommissionReportCreditProductSerializer(s.Serializer):
    bank = BankSerializer()
    credit_product = CreditProductSerializer()
    commission = s.DecimalField(decimal_places=2, max_digits=12)
    sum_cur_month = s.DecimalField(decimal_places=2, max_digits=12)
    sum_period = s.DecimalField(decimal_places=2, max_digits=12)
    sum_all = s.DecimalField(decimal_places=2, max_digits=12)

    class Meta:
        resource_name = 'CommissionReportCreditProduct'


class CommissionReportExtraServiceSerializer(s.Serializer):
    bank = BankSerializer()
    extra_service = ExtraServiceSerializer()
    commission = s.DecimalField(decimal_places=2, max_digits=12)
    sum_cur_month = s.DecimalField(decimal_places=2, max_digits=12)
    sum_period = s.DecimalField(decimal_places=2, max_digits=12)
    sum_all = s.DecimalField(decimal_places=2, max_digits=12)

    class Meta:
        resource_name = 'CommissionReportExtraService'
