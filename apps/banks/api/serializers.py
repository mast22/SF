from rest_framework_json_api import serializers as s
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext as _

from apps.users.const import Roles
from apps.users.models import TerMan
from .. import models as m


class BankSerializer(s.ModelSerializer):
    partners_count = s.IntegerField(read_only=True)
    outlets_count = s.IntegerField(read_only=True)
    agents_count = s.IntegerField(read_only=True)

    class Meta:
        model = m.Bank
        fields = ['name', 'partners_count', 'outlets_count', 'agents_count', 'credit_products', 'extra_services',
                  'logo']
        meta_fields = ('partners_count', 'outlets_count', 'agents_count')
        read_only_fields = ['name', 'logo']

    included_serializers = {
        'credit_products': 'apps.banks.api.serializers.CreditProductSerializer',
        'extra_services': 'apps.banks.api.serializers.ExtraServiceSerializer',
    }



class CreditProductSerializer(s.ModelSerializer):
    commissions_sum = s.DecimalField(read_only=True, decimal_places=2, max_digits=12)
    orders_sum = s.DecimalField(read_only=True, decimal_places=2, max_digits=12)
    included_serializers = {
        'bank': BankSerializer,
        'agent_credit_products': 'apps.banks.api.serializers.AgentCreditProductSerializer',
    }

    class Meta:
        model = m.CreditProduct
        fields = '__all__'
        meta_fields = ('orders_sum', 'commissions_sum',)


class ExtraServiceSerializer(s.ModelSerializer):
    commissions_sum = s.DecimalField(read_only=True, decimal_places=2, max_digits=12)
    orders_sum = s.DecimalField(read_only=True, decimal_places=2, max_digits=12)
    included_serializers = {
        'bank': BankSerializer,
    }

    class Meta:
        model = m.ExtraService
        fields = '__all__'
        meta_fields = ('commissions_sum',)


class TerManBankSerializer(s.ModelSerializer):
    bank = s.ResourceRelatedField(queryset=m.Bank.objects.all())
    ter_man = s.ResourceRelatedField(queryset=TerMan.objects.all())
    terman_credit_products = s.ResourceRelatedField(
        queryset=m.TerManCreditProduct.objects.all(),
        many=True, required=False
    )
    terman_extra_services = s.ResourceRelatedField(
        queryset=m.TerManExtraService.objects.all(),
        many=True, required=False
    )
    current_month_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    all_time_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    period_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)

    included_serializers = {
        'bank': BankSerializer,
        'ter_man': 'apps.users.api.serializers.TerManIncludedSerializer',
        'terman_credit_products': 'apps.banks.api.serializers.TerManCreditProductSerializer',
        'terman_extra_services': 'apps.banks.api.serializers.TerManExtraServiceSerializer',
    }

    class Meta:
        model = m.TerManBank
        fields = ('bank', 'ter_man', 'is_active', 'priority', 'terman_credit_products', 'terman_extra_services')
        meta_fields = ('current_month_total', 'all_time_total', 'period_total',)


class TerManCreditProductSerializer(s.ModelSerializer):
    terman_bank = s.ResourceRelatedField(queryset=m.TerManBank.objects.all())
    credit_product = s.ResourceRelatedField(queryset=m.CreditProduct.objects.all())
    current_month_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    all_time_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    period_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)

    included_serializers = {
        'terman_bank': TerManBankSerializer,
        'credit_product': CreditProductSerializer,
    }

    class Meta:
        model = m.TerManCreditProduct
        fields = '__all__'
        meta_fields = ('all_time_total', 'current_month_total', 'period_total',)


class TerManExtraServiceSerializer(s.ModelSerializer):
    terman_bank = s.ResourceRelatedField(queryset=m.TerManBank.objects.all())
    extra_service = s.ResourceRelatedField(queryset=m.ExtraService.objects.all())
    current_month_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    all_time_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    period_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)

    included_serializers = {
        'terman_bank': TerManBankSerializer,
        'extra_service': ExtraServiceSerializer,
    }

    class Meta:
        model = m.TerManExtraService
        fields = '__all__'
        meta_fields = ('all_time_total', 'current_month_total', 'period_total',)


class AgentBankSerializer(s.ModelSerializer):
    # agent = s.ResourceRelatedField(queryset=Agent.objects.all())
    agent_extra_services = s.ResourceRelatedField(
        queryset=m.AgentExtraService.objects.all(),
        many=True, required=False
    )
    agent_credit_products = s.ResourceRelatedField(
        queryset=m.AgentCreditProduct.objects.all(),
        many=True, required=False
    )
    included_serializers = {
        'agent': 'apps.users.api.serializers.AgentIncludedSerializer',
        'bank': 'apps.banks.api.serializers.BankSerializer',
        'agent_credit_products': 'apps.banks.api.serializers.AgentCreditProductSerializer',
        'agent_extra_services': 'apps.banks.api.serializers.AgentExtraServiceSerializer',
    }
    bank = s.ResourceRelatedField(read_only=True, required=False)

    cps_commission_min = s.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    cps_commission_max = s.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    ess_commission_min = s.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    ess_commission_max = s.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    current_month_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    all_time_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    period_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = m.AgentBank
        fields = '__all__'
        meta_fields = (
            'cps_commission_min', 'cps_commission_max',
            'ess_commission_min', 'ess_commission_max',
            'current_month_total', 'all_time_total', 'period_total',
        )


class AgentCreditProductSerializer(s.ModelSerializer):
    current_month_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    all_time_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    period_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    credit_product = s.ResourceRelatedField(read_only=True)
    terman_credit_product = s.ResourceRelatedField(queryset=m.TerManCreditProduct.objects.all())

    included_serializers = {
        'credit_product': CreditProductSerializer,
        'agent_bank': AgentBankSerializer,
        'terman_credit_product': TerManCreditProductSerializer,
    }

    class Meta:
        model = m.AgentCreditProduct
        fields = '__all__'
        meta_fields = ('all_time_total', 'current_month_total', 'period_total')

    def _check_commission(self, attrs):
        tcp = attrs['terman_credit_product']
        com = attrs['commission']
        c_min = tcp.commission_min
        c_max = tcp.commission_max
        user = self.context['request'].user
        if user.role == Roles.TER_MAN and (com > c_max or com < c_min):
            raise ValidationError(_('Комиссия задана не корректно'))
        return True

    def validate(self, attrs):
        self._check_commission(attrs)
        return attrs


class AgentExtraServiceSerializer(s.ModelSerializer):
    current_month_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    all_time_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    period_total = s.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    extra_service = s.ResourceRelatedField(read_only=True)

    included_serializers = {
        'extra_service': ExtraServiceSerializer,
        'agent_bank': AgentBankSerializer,
    }

    class Meta:
        model = m.AgentExtraService
        fields = '__all__'
        meta_fields = ('all_time_total', 'current_month_total', 'period_total',)

    def _check_commission(self, attrs):
        tcp = attrs['terman_extra_service']
        com = attrs['commission']
        c_min = tcp.commission_min
        c_max = tcp.commission_max
        user = self.context['request'].user
        if user.role == Roles.TER_MAN and (com > c_max or com < c_min):
            raise ValidationError(_('Комиссия задана не корректно'))
        return com

    def validate(self, attrs):
        self._check_commission(attrs)
        return attrs


class OrderChoosableCreditProductsSerializer(s.ModelSerializer):
    agent_commission = s.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    included_serializers = {
        'bank': BankSerializer,
        'agent_bank': AgentBankSerializer,
        'agent_credit_product': AgentCreditProductSerializer,
    }

    class Meta:
        model = m.CreditProduct
        fields = '__all__'



class OrderChoosableExtraServicesSerializer(s.ModelSerializer):
    agent_commission = s.DecimalField(max_digits=5, decimal_places=2)

    included_serializers = {
        'bank': BankSerializer,
        'agent_bank': AgentBankSerializer,
        'agent_extra_service': AgentExtraServiceSerializer,
    }

    class Meta:
        model = m.ExtraService
        fields = '__all__'


class OutletBankSerializer(s.ModelSerializer):
    bank = s.ResourceRelatedField(
        queryset=m.Bank.objects.all()
    )
    included_serializers = {
        'bank': BankSerializer,
        'outlet': 'apps.partners.api.serializers.OutletSerializer',
    }

    class Meta:
        model = m.OutletBank
        fields = '__all__'


class OutletCreditProductSerializer(s.ModelSerializer):
    included_serializers = {
        'outlet_bank': OutletBankSerializer,
        'credit_product': CreditProductSerializer,
    }

    class Meta:
        model = m.OutletCreditProduct
        fields = '__all__'


class OutletExtraServiceSerializer(s.ModelSerializer):
    included_serializers = {
        'outlet_bank': OutletBankSerializer,
        'extra_service': ExtraServiceSerializer,
    }

    class Meta:
        model = m.OutletExtraService
        fields = '__all__'


# class AgentOutletCreditProductSerializer(s.ModelSerializer):
#     class Meta:
#         model = m.AgentOutletCreditProduct
#         fields = '__all__'
#
#     def validate(self, attrs):
#         comms.check_for_min_max(**attrs)
#         return attrs
#
#
# class AgentOutletExtraServiceSerializer(s.ModelSerializer):
#     class Meta:
#         model = m.AgentOutletExtraService
#         fields = '__all__'
#
#     def validate(self, attrs):
#         comms.check_for_min_max(**attrs)
#         return attrs
