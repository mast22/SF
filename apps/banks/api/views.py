from django.db.models import Count, Q, Sum, OuterRef, Subquery, Prefetch, Min, Max, Value, DecimalField
from rest_framework import exceptions as rest_exc
from apps.common.viewsets import ModelViewSet, NoDestroyModelViewSet, ListOnlyModelViewSet, WithStatsMixin
from apps.common import utils as u
from apps.orders.const import OrderStatus
from apps.orders.models import Order, OrderCreditProduct
from .. import models as m
from . import serializers as s
from . import filters as f
from . import permissions as p


class BankViewSet(WithStatsMixin, NoDestroyModelViewSet, ModelViewSet):
    """Банки.
    Использовать параметр with-stats для получения доп. полей в meta.
    with-stats=counts - кол-во партнёров, кол-во агентов, кол-во торговых точек.
    """
    queryset = m.Bank.objects.all()
    serializer_class = s.BankSerializer
    permission_classes = (p.BankAccessPolicy,)
    filterset_fields = ('id', 'name',)
    querysets_with_stats = {
        'counts': 'with_counts',
    }

    def with_counts(self, qs, *args, **kwargs):
        return qs.annotate(
            partners_count=Count('partner_banks__partner_id', filter=Q(partner_banks__is_active=True), distinct=True),
            outlets_count=Count('outlet_banks__outlet_id', filter=Q(outlet_banks__is_active=True), distinct=True),
            agents_count=Count('agent_banks__agent_id', filter=Q(agent_banks__is_active=True), distinct=True),
        )

    prefetch_for_includes = {
        '__all__': [],
        'credit_products': ['credit_products'],
    }
    select_for_includes = {}



class CreditProductViewSet(WithStatsMixin, ModelViewSet):
    """Кредитные продукты банков.
    Использовать параметр with-stats для получения доп. полей в meta:
    with-stats=commission:
        * `orders_sum` - Общая сумма по заявкам для данного КП
        * `commissions_sum` - Сумма процентов агента по заявкам для данного КП
    """
    queryset = m.CreditProduct.objects.all()
    serializer_class = s.CreditProductSerializer
    permission_classes = (p.BankAccessPolicy,)
    filterset_fields = ('id', 'bank', 'is_active',)
    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        return qs.annotate(
            orders_sum=Sum('order_credit_products__orders_chosen__purchase_amount',
                filter=Q(order_credit_products__orders_chosen__status=OrderStatus.AUTHORIZED), distinct=True),
            commissions_sum=Sum('order_credit_products__agent_commission',
                 filter=Q(order_credit_products__orders_chosen__status=OrderStatus.AUTHORIZED), distinct=True),
        )


class ExtraServiceViewSet(WithStatsMixin, ModelViewSet):
    """Дополнительные услуги банков.

    Использовать параметр with-stats=commission для получения доп. полей в meta.
    """
    queryset = m.ExtraService.objects.all()
    serializer_class = s.ExtraServiceSerializer
    permission_classes = (p.BankAccessPolicy,)
    filterset_fields = ('id', 'bank', 'is_active',)
    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        return qs.annotate(commissions_sum=Sum('order_extra_services__agent_commission',
            filter=Q(order_extra_services__order_credit_product__order__status=OrderStatus.AUTHORIZED), distinct=True)
        )



class AgentBankViewSet(WithStatsMixin, ModelViewSet):
    """Привязка агентов к банкам.

    Добавление агента -> Банки и кредитные продукты агента
    Галочки напротив каждого банка. (commission_min/max - не обязательны)

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * cps_commission_min/cps_commission_max - Диапазон комиссии агента по кредитным продуктам банка
        * ess_commission_min/ess_commission_max - Диапазон комиссии агента по доп. услугам банка
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.AgentBank.objects.all()
    serializer_class = s.AgentBankSerializer
    permission_classes = (p.AgentBankAccessPolicy,)
    filterset_fields = ('id', 'agent', 'bank', 'is_active',)
    filterset_class = f.AgentBanksPeriodFilterSet
    prefetch_for_includes = {
        'agent': ('agent',),
        'bank': ('bank',),
        'agent_credit_products': ('agent_credit_products',),
        'agent_extra_services': ('agent_extra_services',),
    }
    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            cps_commission_min=Min('agent_credit_products__commission'),
            cps_commission_max=Max('agent_credit_products__commission'),
            ess_commission_min=Min('agent_extra_services__commission'),
            ess_commission_max=Max('agent_extra_services__commission'),

            current_month_total=Sum(Subquery(OrderCreditProduct.objects.filter(
                orders_chosen__agent_id=OuterRef('agent_id'),
                orders_chosen__status=OrderStatus.AUTHORIZED,
                orders_chosen__created_at__gte=current_month,
            ).values('agent_commission')), distinct=True),
            all_time_total=Sum(Subquery(OrderCreditProduct.objects.filter(
                orders_chosen__agent_id=OuterRef('agent_id'),
                orders_chosen__status=OrderStatus.AUTHORIZED,
            ).values('agent_commission')), distinct=True),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(OrderCreditProduct.objects.filter(
                orders_chosen__agent_id=OuterRef('agent_id'),
                orders_chosen__status=OrderStatus.AUTHORIZED,
                orders_chosen__created_at__range=(date_start, date_end),
            ).values('agent_commission')), distinct=True))
        return qs


class AgentCreditProductViewSet(WithStatsMixin, ModelViewSet):
    """Настройки кредитных продуктов для агентов.

    Новый заказ -> Подбор кредитных программ агентом
    Добавление агента -> Банки и кредитные продукты агента -> Комиссия по кредитным продуктам

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.AgentCreditProduct.objects.all().prefetch_related(
        Prefetch('terman_credit_product', queryset=m.TerManCreditProduct.objects.all(), to_attr='tcp')
    )
    serializer_class = s.AgentCreditProductSerializer
    permission_classes = (p.AgentCreditProductAccessPolicy,)
    filterset_class=f.AgentCPSPeriodFilterSet

    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                agent_id=OuterRef('agent_bank__agent_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__agent_commission')), distinct=True),
            all_time_total=Sum(Subquery(Order.objects.filter(
                agent_id=OuterRef('agent_bank__agent_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__agent_commission')), distinct=True),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                agent_id=OuterRef('agent_bank__agent_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__agent_commission')), distinct=True))
        return qs


class AgentExtraServicesViewSet(WithStatsMixin, ModelViewSet):
    """Настройки доп. услуг для агентов.

    Добавление агента -> Банки и кредитные продукты агента -> Комиссия за дополнительные услуги

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период

    """
    queryset = m.AgentExtraService.objects.all()
    serializer_class = s.AgentExtraServiceSerializer
    permission_classes = (p.AgentExtraServicesAccessPolicy,)
    filterset_class = f.AgentESSPeriodFilterSet

    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                agent_id=OuterRef('agent_bank__agent_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__order_extra_services__agent_commission')), distinct=True),
            all_time_total=Sum(Subquery(Order.objects.filter(
                agent_id=OuterRef('agent_bank__agent_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__order_extra_services__agent_commission')), distinct=True),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                agent_id=OuterRef('agent_bank__agent_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__order_extra_services__agent_commission')), distinct=True))
        return qs


class CreditProductsCalculateViewSet(ListOnlyModelViewSet):
    """Кредитные продукты для кредитного калькулятора.
    Необходимо передать фильтр по agent, чтобы получить его комиссию.
    Пирмер:
    /api/credit-products-calculate/?filter[agent]=5&filter[outlet]=1&filter[initial_payment]=1000&filter[term]=5
    """
    queryset = m.CreditProduct.objects.select_related('bank').all()
    serializer_class = s.OrderChoosableCreditProductsSerializer
    filterset_class = f.CreditProductCalcualteFilterSet
    permission_classes = (p.OrderChoosableCreditProductsAccessPolicy,)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        agent_id = u.get_filter_value('agent', self.request, is_json_api=True, default=None)
        qs = qs.annotate(agent_commission=Subquery(m.AgentCreditProduct.objects.filter(
            agent_bank__agent_id=agent_id,
            credit_product_id=OuterRef('id'),
        ).values('commission'))) \
            if agent_id else qs.annotate(agent_commission=Value(None, DecimalField()))
        return qs

    class JSONAPIMeta:
        resource_name = 'credit-products-calculate'


class OrderChoosableCreditProductsViewSet(ListOnlyModelViewSet):
    """
    Кредитные продукты, которые доступны для добавления в данный заказ. (п.3)
    """
    queryset = m.CreditProduct.objects.select_related('bank').all()
    serializer_class = s.OrderChoosableCreditProductsSerializer
    filterset_class = f.OrderChoosableCreditProductsFilterSet
    permission_classes = (p.OrderChoosableCreditProductsAccessPolicy,)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        order_id = u.get_related_pk('order_pk', 'order', self)
        order = Order.objects.only('id', 'agent_id', 'outlet_id').get(id=order_id) if order_id else None
        if not order_id or order is None:
            raise rest_exc.NotFound()
        qs = qs.filter(
            is_active=True,
            agent_credit_products__is_active=True,
            agent_credit_products__agent_bank__agent_id=order.agent_id,
            agent_credit_products__agent_bank__is_active=True,
            outlet_credit_products__is_active=True,
            outlet_credit_products__outlet_bank__outlet_id=order.outlet_id,
            outlet_credit_products__outlet_bank__is_active=True,
            # FIXME: this filters are temporary disabled - until add fixtures
            # terman_credit_products__is_active=True,
            # terman_credit_products__terman_bank__ter_man_id=agent.ter_man_id,
            # terman_credit_products__terman_bank__is_active=True,
        ).annotate(agent_commission=Subquery(m.AgentCreditProduct.objects.filter(
            agent_bank__agent_id=order.agent_id,
            credit_product_id=OuterRef('id'),
        ).values('commission')))
        return qs


class OrderChoosableExtraServicesViewSet(ListOnlyModelViewSet):
    """
    Дополнительные услуги для добавления в заказ (п.3).
    """
    queryset = m.ExtraService.objects.select_related('bank').all()
    serializer_class = s.OrderChoosableExtraServicesSerializer
    permission_classes = (p.OrderChoosableCreditProductsAccessPolicy,)
    filterset_fields = ('id', 'bank',)
    # filterset_class = f.OrderCreditProductFilterSet

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        order_id = u.get_related_pk('order_pk', 'order', self)
        order = Order.objects.only('id', 'agent_id', 'outlet_id').get(id=order_id) if order_id else None
        if not order_id or order is None:
            raise rest_exc.NotFound()
        qs = qs.filter(
            is_active=True,
            agent_extra_services__is_active=True,
            agent_extra_services__agent_bank__agent_id=order.agent_id,
            agent_extra_services__agent_bank__is_active=True,
            outlet_extra_services__is_active=True,
            outlet_extra_services__outlet_bank__outlet_id=order.outlet_id,
            outlet_extra_services__outlet_bank__is_active=True,
            # FIXME: this filters are temporary disabled - until add fixtures
            # terman_credit_products__is_active=True,
            # terman_credit_products__terman_bank__ter_man_id=agent.ter_man_id,
            # terman_credit_products__terman_bank__is_active=True,
        ).annotate(agent_commission=Subquery(m.AgentExtraService.objects.filter(
            agent_bank__agent_id=order.agent_id,
            extra_service_id=OuterRef('id'),
        ).values('commission')))
        # qs = qs.annotate_with(current_order=order, current_agent=agent)
        return qs



class OutletBankViewSet(WithStatsMixin, ModelViewSet):
    """Привязка торговых точек к банкам.

    Добавление торговой точки -> Банки и кредитные программы и комиссия ->
    Галочки напротив каждого банка. (commission_min/max - не обязательны)
    /api/order/{id}/credit-products/?first_pay=1500&term=10
    /api/order/{id}/credit-products/?first_pay__not=1500&term__not=10

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.OutletBank.objects.all()
    serializer_class = s.OutletBankSerializer
    permission_classes = (p.OutletBankAccessPolicy,)
    filterset_fields = ('id', 'outlet', 'bank', 'is_active',)
    prefetch_for_includes = {
        'outlet': ('outlet',),
        'bank': ('bank',),
        'outlet_credit_products': ('outlet_credit_products',),
        'outlet_extra_services': ('outlet_extra_services',),
    }
    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            cps_commission_min=Min('outlet_credit_products__credit_product__agent_credit_products__commission'),
            cps_commission_max=Max('outlet_credit_products__credit_product__agent_credit_products__commission'),
            ess_commission_min=Min('outlet_extra_services__extra_service__agent_extra_services__commission'),
            ess_commission_max=Max('outlet_extra_services__extra_service__agent_extra_services__commission'),
            current_month_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__agent_commission'))),
            all_time_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__agent_commission'))),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__agent_commission'))))
        return qs


class OutletCreditProductsViewSet(WithStatsMixin, ModelViewSet):
    """Настройки кредитных продуктов для торговых точек.

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.OutletCreditProduct.objects.all()
    serializer_class = s.OutletCreditProductSerializer
    permission_classes = (p.OutletCreditProductsAccessPolicy,)
    filterset_fields = ('id', 'outlet_bank', 'credit_product', 'is_active',)
    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_bank__outlet_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__agent_commission'))),
            all_time_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_bank__outlet_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__agent_commission'))),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__agent_commission'))))
        return qs


class OutletExtraServicesViewSet(WithStatsMixin, ModelViewSet):
    """Настройки дополнительных услуг для торговых точек.

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.OutletExtraService.objects.all()
    serializer_class = s.OutletExtraServiceSerializer
    permission_classes = (p.OutletCreditProductsAccessPolicy,)
    filterset_fields = ('id', 'outlet_bank', 'extra_service', 'is_active',)
    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_bank__outlet_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__order_extra_services__agent_commission'))),
            all_time_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_bank__outlet_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__order_extra_services__agent_commission'))),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                outlet_id=OuterRef('outlet_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__order_extra_services__agent_commission'))))
        return qs



class TerManBankViewSet(WithStatsMixin, ModelViewSet):
    """Настройки банков для территориального менеджера.

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.TerManBank.objects.all()
    serializer_class = s.TerManBankSerializer
    permission_classes = (p.TerManBankAccessPolicy,)
    filterset_fields = ('id', 'ter_man', 'bank', 'is_active',)

    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('ter_man_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__terman_commission')), distinct=True),
            all_time_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('ter_man_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__terman_commission')), distinct=True),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('ter_man_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__terman_commission')), distinct=True))
        return qs


class TerManCreditProductViewSet(WithStatsMixin, ModelViewSet):
    """Настройки кредитных продуктов для территориального менеджера.

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.TerManCreditProduct.objects.all()
    serializer_class = s.TerManCreditProductSerializer
    permission_classes = (p.TerManCreditProductAccessPolicy,)
    filterset_fields = ('id', 'terman_bank', 'credit_product', 'is_active')

    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('terman_bank__ter_man_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__terman_commission')), distinct=True),
            all_time_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('terman_bank__ter_man_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__terman_commission')), distinct=True),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('terman_bank__ter_man_id'),
                chosen_product__credit_product_id=OuterRef('credit_product_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__terman_commission')), distinct=True))
        return qs


class TerManExtraServiceViewSet(WithStatsMixin, ModelViewSet):
    """Настройки дополнительных услуг для территориального менеджера.

    Параметр ?with-stats=commission добавит в ответ meta-поля:
        * current_month_total - Сумма процентов по кредитам, выданных в текущем месяце
        * all_time_total - Общая начисленная сумма процентов за выданные кредиты
    Если передать фильтр date_start - date_end, то появится ещё доп. meta-поле:
        * period_total - Сумма процентов по кредитам, выданным за заданный период
    """
    queryset = m.TerManExtraService.objects.all()
    serializer_class = s.TerManExtraServiceSerializer
    permission_classes = (p.TerManCreditProductAccessPolicy,)
    filterset_fields = ('id', 'terman_bank', 'extra_service', 'is_active')

    querysets_with_stats = {
        'commission': 'with_commission'
    }

    def with_commission(self, qs, *args, **kwargs):
        current_month = u.get_current_month()
        date_start = u.get_filter_value('date_start', self.request, is_json_api=True)
        date_end = u.get_filter_value('date_end', self.request, is_json_api=True)
        qs = qs.annotate(
            current_month_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('terman_bank__ter_man_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__gte=current_month,
            ).values('chosen_product__order_extra_services__terman_commission')), distinct=True),
            all_time_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('terman_bank__ter_man_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
            ).values('chosen_product__order_extra_services__terman_commission')), distinct=True),
        )
        if date_start and date_end:
            qs = qs.annotate(period_total=Sum(Subquery(Order.objects.filter(
                agent__ter_man_id=OuterRef('terman_bank__ter_man_id'),
                chosen_product__extra_services__id=OuterRef('extra_service_id'),
                status=OrderStatus.AUTHORIZED,
                created_at__range=(date_start, date_end),
            ).values('chosen_product__order_extra_services__terman_commission')), distinct=True))
        return qs
