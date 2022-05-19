import copy
from django.utils.translation import gettext_lazy as __, gettext as _
from django.utils import timezone as tz
from drf_renderer_xlsx.renderers import XLSXRenderer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import AllowAny
from drf_renderer_xlsx.mixins import XLSXFileMixin

from apps.common.exceptions import BadStateException
from apps.common.transitions import change_state
from apps.common.viewsets import ModelViewSet, ReadOnlyModelViewSet, DEFAULT_ACTIONS
from apps.common.renderers import QRCodePNGRenderer, QRCodeSVGRenderer
from apps.orders.const import OrderStatus
from apps.orders.models import TelegramOrder
from apps.partners.models import Outlet
from apps.orders.api import serializers as s
from apps.orders.api import permissions as p
from apps.orders.api import filters as f
from apps.orders import const as c
from apps.orders import models as m


class OrderViewSet(ModelViewSet):
    """ Модель заказа

    Каждая модель, относящаяся к order является моделью, которая полностью заполняется
    на соответствующем ей шаге. Таким образом, на каждом мы создаём как минимум один объект
    для заполнения заказа и эти самым мы отмечаем прогресс её создания.
    """
    queryset = m.Order.objects.all()
    serializer_class = s.OrderSerializer
    permission_classes = (p.OrderAccessPolicy,)
    custom_serializer_classes = {
        'telegram_order': s.TelegramOrderSerializer,
        'choose_credit_product': s.ChooseCreditProductSerializer,
        'send_documents': s.OrderSendDocumentsSeriazlier,
        'send_to_scoring': s.OrderSendToScoringSerializer,
        'send_to_authorization': s.OrderSendToAuthorizationSerializer,
        'get_contract_qrcode': s.OrderTempTokenSerializer,
        'get_upload_passport_qrcode': s.OrderTempTokenSerializer,
        'clone_order': s.OrderSerializer,
        'update': s.UpdateOrderSerializer,
        'partial_update': s.UpdateOrderSerializer,
    }
    custom_querysets = {
        'get_current_status': m.Order.objects.all().only('id', 'status', 'changed_at')
    }
    filterset_class = f.OrderFilter
    search_fields = (
        'client_order__phone',
        'passport__first_name',
        'passport__last_name',
        'passport__middle_name'
    )

    prefetch_for_includes = {
        '__all__': ['goods', 'history', 'credit_products', 'order_credit_products',],
    }
    select_for_includes = {
        '__all__': [
            'passport', 'personal_data', 'family_data', 'career_education', 'extra_data', 'credit',
        ]
    }
    json_api_actions = DEFAULT_ACTIONS | {'clone_order',}

    @action(detail=True, methods=('POST',))
    def send_to_scoring(self, request, pk=None):
        """ Отправляет заказ на скоринг """
        order = self.get_object()
        change_state(order.set_scoring, __('Невозможно отправить заявку на скоринг'))
        order.save()
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=('POST',))
    def send_client_refused(self, request, pk=None):
        """ Помечает заказ как отклоненный пользователем """
        order = self.get_object()
        change_state(
            order.set_client_refused, __('Невозможно отклонить заявку cо статусом ') + f'"{order.get_status_display()}"'
        )
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',))
    def choose_credit_product(self, request, pk=None):
        """Выбираем конкретный кредитный продукт по окончанию скоринга"""
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_state(
            order.set_agreement,
            _('Невозможно выбрать кредитный продукт') + f' "{order.get_status_display()}" order.chosen',
            chosen_product=serializer.validated_data['chosen_product']
        )
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',))
    def send_documents(self, request, pk=None):
        """ Отправляет в банк подписанные документы."""
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_state(
            order.set_documents_sending,
            _('Невозможно добавить контракт с текущего статуса ') + f'"{order.get_status_display()}"',
            contract=serializer.validated_data['contract']
        )
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',))
    def send_to_authorization(self, request, pk=None):
        """Отправляет в банк запрос на подтверждение авторизации от клиента."""
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_state(
            order.set_authorization,
            _('Невозможно отправить подтверждение авторизации из статуса: ') + f'"{order.get_status_display()}"',
        )
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=True, renderer_classes=(JSONRenderer, QRCodePNGRenderer, QRCodeSVGRenderer,))
    def get_contract_qrcode(self, request, pk=None):
        """Получить qr-код для документов. (Доступно только территориалу)."""
        order = self.get_object()
        token, _ = m.OrderTempToken.objects.get_or_create(order=order, type=c.OrderTempTokenType.PASSPORT)
        serializer = self.get_serializer(token)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=('GET',), detail=True, renderer_classes=(JSONRenderer, QRCodePNGRenderer, QRCodeSVGRenderer,))
    def get_upload_passport_qrcode(self, request, pk=None, *args, **kwargs):
        """Получить qr-код для загрузки паспортных данных"""
        order = self.get_object()
        token, _ = m.OrderTempToken.objects.get_or_create(order=order, type=c.OrderTempTokenType.PASSPORT)
        serializer = self.get_serializer(token)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def recreate_instance(self, new_instance, new_order_id: int):
        """ Создаёт копию вхождения и присваивает новому заказу """
        if new_instance is not None:
            new_instance.pk = None
            new_instance.order_id = new_order_id
            new_instance.save()
        return new_instance

    @action(detail=True, methods=('POST',))
    def reset_status_to_new(self, request, pk=None):
        """ Сбрасывает заказ до первоначального вида для повторного заполнения """
        order = self.get_object()
        change_state(
            order.reset_new, __('Невозможно начать заново заявку со статусом ') + f'"{order.get_status_display()}"'
        )
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=True)
    def clone_order(self, request, pk=None, *args, **kwargs):
        """ Копирует объект заказа и создаёт аналогичный для редактирования
        """
        order = self.get_object()
        if not order.has_ever_been_scored():
            raise BadStateException('Нельзя клонировать заказ, который ни разу не был отправлен на скоринг')

        # Освобождаем копируемый order от данных пользователя чтобы не сломать one_to_one ограничение
        new_order = copy.copy(order)
        new_credit = order.credit
        new_family_data = order.family_data
        new_personal_data = order.personal_data
        new_passport = order.passport
        new_career_education = order.career_education
        new_extra_data = order.extra_data

        new_order.pk = None
        new_order.credit = None
        new_order.family_data = None
        new_order.personal_data = None
        new_order.passport = None
        new_order.career_education = None
        new_order.extra_data = None

        new_client_order = order.client_order
        new_client_order.pk = None
        new_client_order.save()

        new_order.client_order = new_client_order
        new_order.save()

        # Копируем персональные данные
        new_order.credit = self.recreate_instance(new_credit, new_order.id)
        new_order.family_data = self.recreate_instance(new_family_data, new_order.id)
        new_order.personal_data = self.recreate_instance(new_personal_data, new_order.id)
        new_order.passport = self.recreate_instance(new_passport, new_order.id)
        new_order.career_education = self.recreate_instance(new_career_education, new_order.id)
        new_order.extra_data = self.recreate_instance(new_extra_data, new_order.id)
        new_order.status = OrderStatus.NEW
        new_order.save()

        order_goods = order.goods.all()
        new_order_goods = []
        for good in order_goods:
            good.pk = None
            good.order = new_order
            new_order_goods.append(good)

        m.OrderGood.objects.bulk_create(new_order_goods)

        serializer = self.get_serializer(new_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class XLSXOrderList(XLSXFileMixin, ListAPIView):
    """ Выгрузка заказов в xlsx формате.

    Отдельный endpoint c дополнительной фильтраций заказов, которые не достигли скоринга
    """
    swagger_schema = None # FIXME исключаем xlsx из индексации свагером, поскольку ListAPIView ломает json_api_drf_yasg
    queryset = m.Order.objects.order_by('-created_at')
    permission_classes = (p.OrderAccessPolicy,)
    serializer_class = s.XLSXOrderSerializer
    renderer_classes = (XLSXRenderer,)
    column_header = {'titles': list(c.order_xlsx_fields.values())}
    filterset_class = f.XLSXOrderFilter
    filterset_fields = ('outlet__region',)


class TelegramOrderViewSet(ReadOnlyModelViewSet):
    """Модель заказа, полученная из телеграмм бота

    Описание работы
    """
    queryset = m.TelegramOrder.objects.filter(
        created_at__gte=tz.now().replace(hour=0, minute=0, second=0, microsecond=0))  # Отображаются только сегодняшние
    serializer_class = s.TelegramOrderSerializer
    filterset_class = f.TelegramOrdersFilters
    permission_classes = (p.TelegramOrderAccessPolicy,)

    @action(detail=False, methods=('POST',), parser_classes=(MultiPartParser,), permission_classes=(AllowAny,))
    def create_multipart(self, request, *args, **kwargs):
        serializer = s.CreateTelegramOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        outlet_identifier: str = data['api_id']
        del data['api_id']
        outlet = Outlet.objects.filter(telegram_id=outlet_identifier).first()
        if outlet is not None:
            TelegramOrder.objects.create(**data, outlet=outlet)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class OrderHistoryViewSet(ModelViewSet):
    """История заявки и кредитных продуктов в заявке."""
    queryset = m.OrderHistory.objects.all()
    serializer_class = s.OrderHistorySerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'credit_product',)
