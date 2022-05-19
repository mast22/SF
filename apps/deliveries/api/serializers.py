from rest_framework_json_api import serializers as s
from rest_framework.serializers import Serializer
from apps.orders.models import Contract

from .. import models as m


class AddDeliverySerializer(Serializer):
    order_number = s.CharField()


class DeliverySerializer(s.ModelSerializer):
    contracts = s.ResourceRelatedField(queryset=Contract.objects, many=True, required=False)
    included_serializers = {
        'contracts': 'apps.orders.api.serializers.ContractSerializer',
    }

    class Meta:
        model = m.Delivery
        fields = ['id', 'last_modified', 'location', 'contracts']
