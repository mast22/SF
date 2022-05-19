from django.utils.translation import gettext_lazy as __
import django_filters as df
from django.db.models import Q
from apps.common.filters import FilterSet
from apps.common.utils import datetime_as_day
from .. import models as m
from ..const import OrderStatus


class OrderFilter(FilterSet):
    created_at_after = df.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = df.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    today = df.BooleanFilter(field_name='created_at', method='today_filter', label=__('Только за сегодня'))

    class Meta:
        model = m.Order
        fields = [
            'id', 'created_at_after', 'created_at_before', 'today',
            'agent', 'agent__ter_man', 'outlet', 'outlet__partner__region', 'outlet__name',
            'chosen_product', 'chosen_product__credit_product',
            'chosen_product__credit_product__bank', 'status',
        ]

    @staticmethod
    def today_filter(queryset, name, value):
        cur_moment = datetime_as_day()
        return queryset.filter(created_at__gte=cur_moment) if value else queryset


class XLSXOrderFilter(FilterSet):
    created_at_after = df.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = df.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    successful = df.BooleanFilter(method='filter_successful', label=__('Успешные заказы'))

    @staticmethod
    def filter_successful(queryset, name, value):
        """ Фильтрация успешных заказов
        успешные - завершившиеся выдачей кредита, неуспешные - завершившиеся неудачно
        Ни к тем, ни к другим не относятся заказы, которые ещё находятся в процессе оформления
        """
        if value:
            return queryset.filter(status=OrderStatus.AUTHORIZED, chosen_product__isnull=False)
        return queryset.filter(status__in=[OrderStatus.REJECTED, OrderStatus.UNAUTHORIZED, OrderStatus.CLIENT_REFUSED])

    class Meta:
        model = m.Order
        fields = ['created_at_after', 'created_at_before', 'outlet__partner__region']


class ClientFilterSet(FilterSet):
    phone = df.CharFilter()
    latest = df.BooleanFilter(method='latest_filter')

    class Meta:
        model = m.Client
        fields = ('id', 'phone', 'latest')

    @staticmethod
    def phone_filter(queryset, name, value):
        filters = dict(
            initial_payment_min__lte=value,
            initial_payment_max__gte=value,
        ) if name == 'initial_payment' else {}
        return filters

    @staticmethod
    def latest_filter(queryset, name, value):
        if name == 'latest_filter' and value:
            queryset = queryset.filter()
        filters = dict(
            term_min__lte=value,
            term_max__gte=value,
        ) if name == 'term' else {}
        return filters


class TelegramOrdersFilters(FilterSet):
    """"""
    is_free = df.BooleanFilter('order', lookup_expr='isnull', label=__('Свободен'))
    # order = df.ModelChoiceFilter('order', queryset=m.Order.objects.all())
    # outlet = df.ModelChoiceFilter('outlet', queryset=Outlet.objects.all())
    # is_assigned = df.BooleanFilter('is_assigned')

    class Meta:
        model = m.TelegramOrder
        fields = ('id', 'is_free', 'order', 'outlet', 'order__agent',)

