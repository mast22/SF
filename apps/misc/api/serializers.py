from rest_framework_json_api import serializers as s
from ..models import MesaBank
from ..models.accordance import Accordance


class MesaBankSerializer(s.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = MesaBank


class AccordanceSerializer(s.ModelSerializer):
    """ Мы должны подстроить новый интерфейс под старый вариант чтобы не сломать клиентов """
    value = s.CharField(source='desc')

    class Meta:
        fields = ['value', 'desc', 'collection']
        model = Accordance
