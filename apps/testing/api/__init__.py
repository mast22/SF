from rest_framework import permissions as rfp
from rest_framework import serializers as s
from apps.common.viewsets import ModelViewSet

from .. import models as m
from ..models import DummyMessage


class DummyMessageSeriliazer(s.ModelSerializer):
    class Meta:
        model = DummyMessage
        fields = '__all__'


class DummyMessageViewSet(ModelViewSet):
    """
    Здесь хранятся сообщения, отправенные через Dummy провайдера для целей тестирования.
    """
    serializer_class = DummyMessageSeriliazer
    queryset = m.DummyMessage.objects.all()

    permission_classes = (rfp.IsAuthenticated,)
    search_fields = ('subject', 'message', 'sender', 'receiver')
    ordering_fields = '__all__'
    ordering = '-id'
