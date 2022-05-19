import django_filters as df
from django.utils.translation import gettext_lazy as __
from .. import models as m
from apps.common.filters import FilterSet
from apps.users.models.user import Agent
from apps.partners.models.outlet import Outlet


class AgentBanksPeriodFilterSet(FilterSet):
    date_start = df.DateTimeFilter(method=lambda qs, n, v: qs, label=__('Статистика за период. От'))
    date_end = df.DateTimeFilter(method=lambda qs, n, v: qs, label=__('Статистика за период. До'))

    class Meta:
        model = m.AgentBank
        fields = ('id', 'agent', 'bank', 'is_active', 'date_start', 'date_end')


class AgentCPSPeriodFilterSet(FilterSet):
    date_start = df.DateTimeFilter(method=lambda qs, n, v: qs, label=__('Статистика за период. От'))
    date_end = df.DateTimeFilter(method=lambda qs, n, v: qs, label=__('Статистика за период. До'))

    class Meta:
        model = m.AgentCreditProduct
        fields = ('id', 'agent_bank', 'credit_product', 'is_active', 'date_start', 'date_end')


class AgentESSPeriodFilterSet(FilterSet):
    date_start = df.DateTimeFilter(method=lambda qs, n, v: qs, label=__('Статистика за период. От'))
    date_end = df.DateTimeFilter(method=lambda qs, n, v: qs, label=__('Статистика за период. До'))

    class Meta:
        model = m.AgentExtraService
        fields = ('id', 'agent_bank', 'agent_bank__agent', 'extra_service', 'is_active', 'date_start', 'date_end')



class OrderChoosableCreditProductsFilterSet(FilterSet):
    initial_payment = df.NumberFilter(method='initial_payment_filter', label=__('Первоначальный платёж'))
    term = df.NumberFilter(method='term_filter', label=__('Срок кредита'))
    agent_bank__agent = df.ModelChoiceFilter(queryset=Agent.objects.all(), label=__('Агент'))

    class Meta:
        model = m.CreditProduct
        fields = ('id', 'initial_payment', 'term', 'agent_bank__agent')
        grouped_filters = ('initial_payment', 'term')

    @staticmethod
    def initial_payment_filter(queryset, name, value):
        filters = dict(
            initial_payment_min__lte=value,
            initial_payment_max__gte=value,
        ) if name == 'initial_payment' else {}
        return filters

    @staticmethod
    def term_filter(queryset, name, value):
        filters = dict(
            term_min__lte=value,
            term_max__gte=value,
        ) if name == 'term' else {}
        return filters


class CreditProductCalcualteFilterSet(FilterSet):
    initial_payment = df.NumberFilter(method='initial_payment_filter', label=__('Первоначальный платёж'))
    term = df.NumberFilter(method='term_filter', label=__('Срок кредита'))
    agent = df.ModelChoiceFilter(queryset=Agent.objects.all(), method='agent_filter', label=__('Агент'))
    outlet = df.ModelChoiceFilter(queryset=Outlet.objects.all(), method='outlet_filter',
            label=__('Торговая точка'))

    class Meta:
        model = m.CreditProduct
        fields = ('id', 'initial_payment', 'term', 'agent', 'outlet',)
        grouped_filters = ('initial_payment', 'term', 'agent', 'outlet',)

    @staticmethod
    def initial_payment_filter(queryset, name, value):
        filters = dict(
            initial_payment_min__lte=value,
            initial_payment_max__gte=value,
        ) if name == 'initial_payment' and value is not None else {}
        return filters

    @staticmethod
    def term_filter(queryset, name, value):
        filters = dict(
            term_min__lte=value,
            term_max__gte=value,
        ) if name == 'term' and value is not None else {}
        return filters

    @staticmethod
    def agent_filter(queryset, name, value):
        filters = dict(
            is_active=True,
            agent_credit_products__is_active=True,
            agent_credit_products__agent_bank__agent_id=value,
            agent_credit_products__agent_bank__is_active=True,
        ) if name == 'agent' and value is not None else {}
        return filters

    @staticmethod
    def outlet_filter(queryset, name, value):
        filters = dict(
            outlet_credit_products__is_active=True,
            outlet_credit_products__outlet_bank__outlet_id=value,
            outlet_credit_products__outlet_bank__is_active=True,
        ) if name == 'outlet' and value is not None else {}
        return filters
