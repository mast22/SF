from apps.common.viewsets import ModelViewSet
from ..models import MesaBank
from .serializers import MesaBankSerializer, AccordanceSerializer
from . import permissions as p
from ..models.accordance import Accordance
from ...common.permissions.permissions import IsAuthenticated


class AccordanceViewSet(ModelViewSet):
    serializer_class = AccordanceSerializer
    queryset = Accordance.objects.all()
    filterset_fields = ['collection',]
    permission_classes = (IsAuthenticated,)
    search_fields = ('desc',)


class MesaBankViewSet(ModelViewSet):
    """Банки. Дополнительная сущность для заполнения поля Банк у партнёров
    и других мест, где требуется банк не ради кредитных продуктов."""
    serializer_class = MesaBankSerializer
    queryset = MesaBank.objects.all()
    permission_classes = (p.MesaBankAccessPolicy,)
    filterset_fields = ['name',]
