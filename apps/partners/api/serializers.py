from rest_framework_json_api import serializers as s
from apps.users.api.serializers import TerManIncludedSerializer, AgentIncludedSerializer
from apps.banks.api.serializers import BankSerializer
from apps.banks.models import OutletBank
from .. import models as m
from apps.users.models.user import Agent, TerMan


class PartnerSerializer(s.ModelSerializer):
    outlets = s.ResourceRelatedField(queryset=m.Outlet.objects, many=True, required=False)
    ter_man = s.ResourceRelatedField(queryset=TerMan.objects)
    included_serializers = {
        'outlets': 'apps.partners.api.serializers.OutletSerializer',
        'region': 'apps.partners.api.serializers.RegionSerializer',
        'ter_man': 'apps.users.api.serializers.TerManSerializer',
    }

    class Meta:
        fields = '__all__'
        model = m.Partner


class OutletSerializer(s.ModelSerializer):
    banks = s.ResourceRelatedField(queryset=m.Outlet.objects, many=True, required=False)
    agents = s.ResourceRelatedField(queryset=Agent.objects, many=True, required=False)
    outlet_agents = s.ResourceRelatedField(queryset=m.OutletAgent.objects, many=True, required=False)
    outlet_banks = s.ResourceRelatedField(queryset=OutletBank.objects, many=True, required=False)
    orders_count = s.IntegerField(read_only=True)

    included_serializers = {
        'banks': BankSerializer,
        'agents': AgentIncludedSerializer,
        'outlet_agents': 'apps.partners.api.serializers.OutletAgentSerializer',
        'outlet_banks': 'apps.banks.api.serializers.OutletBankSerializer',
        'partner': 'apps.partners.api.serializers.PartnerSerializer',
        'address': 'apps.partners.api.serializers.LocationSerializer',
    }

    class Meta:
        model = m.Outlet
        fields = '__all__'
        meta_fields = ('orders_count',)


class OutletAgentSerializer(s.ModelSerializer):
    included_serializers = {
        'agent': AgentIncludedSerializer,
        'outlet': OutletSerializer,
    }

    class Meta:
        fields = '__all__'
        model = m.OutletAgent


class LocationSerializer(s.ModelSerializer):
    postcode = s.CharField(min_length=6, max_length=6)
    class Meta:
        model = m.Location
        fields = '__all__'


class RegionSerializer(s.ModelSerializer):
    partners = s.ResourceRelatedField(
        queryset=m.Partner.objects,
        many=True, required=False,
    )
    ter_mans = s.ResourceRelatedField(
        queryset=TerMan.objects,
        many=True, required=False,
    )
    # outlets = s.ResourceRelatedField(
    #     queryset=m.Outlet.objects,
    #     many=True, required=False,
    # )
    included_serializers = {
        'partners': PartnerSerializer,
        'ter_mans': TerManIncludedSerializer,
        # 'outlets': OutletSerializer,
    }

    class Meta:
        fields = '__all__'
        model = m.Region


class PartnerBankSerializer(s.ModelSerializer):
    class Meta:
        model = m.PartnerBank
        fields = '__all__'
