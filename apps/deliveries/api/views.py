from apps.common.viewsets import ModelViewSet, DEFAULT_ACTIONS
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .. import models as m
from .. import tasks as t
from . import serializers as s
from . import permissions as p


class DeliveryViewSet(ModelViewSet):
    serializer_class = s.DeliverySerializer
    queryset = m.Delivery.objects.all()
    permission_classes = (p.DeliveryAccessPolicy,)
    filterset_fields = ('location', 'cdek_uuid',)
    search_fields = ('cdek_number',)

    prefetch_for_includes = {
        '__all__': ['contracts'],
    }

    custom_serializer_classes = {
        'add_delivery': s.AddDeliverySerializer
    }

    @swagger_auto_schema(responses={204: 'No content'})
    @action(detail=False, methods=('post',))
    def add_delivery(self, request, pk=None):
        """ Запрашиваем информацию по доставке с сайта СДЭК
        Запускает валидацию номера и проверяет его статус
        """
        add_delivery_serializer = self.get_serializer(data=request.data)
        add_delivery_serializer.is_valid(raise_exception=True)
        t.validate_and_create_delivery(add_delivery_serializer.validated_data['order_number'])
        return Response(status=204)
