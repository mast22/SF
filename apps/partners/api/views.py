from django.db.models import Count, Sum, OuterRef, Subquery, Min, Max
from apps.common.viewsets import ModelViewSet, WithStatsMixin
from apps.common import utils as u
from apps.orders.const import OrderStatus
from apps.orders.models import Order
from .. import models as m
from . import serializers as s
from . import permissions as p


class RegionViewSet(WithStatsMixin, ModelViewSet):
    """Регионы.
    with-stats=counts - Добавит в meta количество партнёров и торговых точек в данном регионе.
    """
    queryset = m.Region.objects.all()
    serializer_class = s.RegionSerializer
    permission_classes = (p.RegionAccessPolicy,)
    filterset_fields = ('id', 'acc_man', 'is_active', 'ter_mans', 'partners__outlets')
    search_fields = ('name',)

    prefetch_for_includes = {
        '__all__': ['partners',],
        'partners.outlets': ['partners__outlets',],
    }
    select_for_includes = {
        '__all__': ['acc_man',]
    }
    querysets_with_stats = {
        'counts': 'with_counts'
    }

    def with_counts(self, qs, *args, **kwargs):
        return qs.annotate(
            partners_count=Count('partners__id', distinct=True),
            outlets_count=Count('partners__outlets__id', distinct=True),
        )


class PartnerViewSet(WithStatsMixin, ModelViewSet):
    """Патнёры.

    with-stats=outlets_count - добавит в meta количество торговых точек у данного партнёра."""
    queryset = m.Partner.objects.all()
    serializer_class = s.PartnerSerializer
    permission_classes = (p.PartnerAccessPolicy,)
    filterset_fields = ('id', 'region', 'is_active', 'bank', 'ter_man', 'outlets')
    search_fields = ('name', 'legal_name')

    select_for_includes = {
        'partner': ['partner',]
    }
    querysets_with_stats = {
        'outlets_count': 'with_outlets_count'
    }

    def with_outlets_count(self, qs, *args, **kwargs):
        return qs.annotate(outlets_count=Count('outlets__id'))



class OutletViewSet(WithStatsMixin, ModelViewSet):
    """Торговые точки.

    with-stats=counts - добавит в meta количество заявок и агентов на данной торговой точке.
    """
    queryset = m.Outlet.objects.all().prefetch_related('banks', 'agents', 'outlet_agents', 'outlet_banks')
    serializer_class = s.OutletSerializer
    permission_classes = (p.OutletAccessPolicy,)
    filterset_fields = ('id', 'partner', 'partner__region', 'address', 'partner__ter_man', 'status', 'agents')
    search_fields = ('name', 'address__locality', 'address__street')
    querysets_with_stats = {
        'orders_count': 'with_orders_count',
        'counts': 'with_counts',
    }

    def with_orders_count(self, qs, *args, **kwargs):
        return qs.annotate(
            orders_count=Count('orders__id', distinct=True),
            agents_count=Count('outlet_agents__agent_id', distinct=True)
        )


class OutletAgentViewSet(ModelViewSet):
    """Привязка агентов к торговым точкам."""
    queryset = m.OutletAgent.objects.all()
    serializer_class = s.OutletAgentSerializer
    permission_classes = (p.OutletAgentAccessPolicy,)
    filterset_fields = ('id', 'outlet', 'agent', 'is_active')
    search_fields = ('name',)



class LocationViewSet(ModelViewSet):
    """Адрес."""
    queryset = m.Location.objects.all()
    serializer_class = s.LocationSerializer
    permission_classes = (p.LocationAccessPolicy,)
    filterset_fields = ('id', 'subject')
    search_fields = ('street', 'house', 'building', 'place', 'postcode')


class PartnerBankViewSet(ModelViewSet):
    """Привязка партнёров к банкам."""
    queryset = m.PartnerBank.objects.all()
    serializer_class = s.PartnerBankSerializer
    permission_classes = (p.PartnerBankAccessPolicy,)
    filterset_fields = ('id', 'partner', 'bank', 'is_active')
