from apps.common.viewsets import ModelViewSet
from apps.orders import models as m
from apps.orders.api import serializers as s
from apps.orders.api import permissions as p


class OrderCreditProductViewSet(ModelViewSet):
    """Кредитные продукты в заявке"""
    queryset = m.OrderCreditProduct.objects.prefetch_related('order_extra_services', 'extra_services').all()
    serializer_class = s.OrderCreditProductSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'credit_product', 'status',)


class OrderExtraServiceViewSet(ModelViewSet):
    """Доп. услуги, назначенные на кредитный продукт в заявке"""
    queryset = m.OrderExtraService.objects.all()
    serializer_class = s.OrderExtraServiceSerializer
    permission_classes = (p.OrderExtraServiceAccessPolicy,)
    filterset_fields = ('id', 'extra_service', 'order_credit_product', 'order_credit_product__order')
