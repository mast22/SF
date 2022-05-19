from django.utils.translation import gettext_lazy as __
from rest_framework import exceptions as rest_exc
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.common.exceptions import BadStateException
from apps.common.viewsets import ModelViewSet
from apps.orders import models as m, const as c
from apps.orders.api import serializers as s
from apps.orders.api import permissions as p


class CanClientDataBeModifiedMixin:
    """
    Данные клиента можно редактировать только во время оформления заказа
    Заказ оформляется когда находится в статусе "Новый"
    """
    def update(self, request, *args, **kwargs):
        order = self.get_object().order
        if order and order.status != c.OrderStatus.NEW:
            raise BadStateException(detail=__('Данные клиента можно редактировать только во время оформления заказа'))
        return super(CanClientDataBeModifiedMixin, self).update(request, *args, **kwargs)


class GoodViewSet(ModelViewSet):
    """Товары."""
    queryset = m.Good.objects.all()
    serializer_class = s.GoodSerializer
    filterset_fields = ('id', 'category',)
    search_fields = ('brand', 'model', 'name',)


class OrderGoodViewSet(ModelViewSet):
    """Товары в заказе."""
    queryset = m.OrderGood.objects.all()
    serializer_class = s.OrderGoodSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'good', 'order', 'good__category', 'serial_number')
    search_fields = ('serial_number', 'good__brand', 'good__model', 'good__name',)


class OrderGoodServicesViewSet(ModelViewSet):
    """Программы услуг для товара."""
    queryset = m.OrderGoodService.objects.all()
    serializer_class = s.OrderGoodServiceSerializer
    filterset_fields = ('id', 'type', 'order_good')
    search_fields = ('type__value', 'type__desc',)


class CreditViewSet(CanClientDataBeModifiedMixin, ModelViewSet):
    """Информация о кредите: срок, первоначальный взнос, etc"""
    queryset = m.Credit.objects.all()
    serializer_class = s.CreditSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'client')
    prefetch_for_includes = {
        '__all__': ['client', 'order', ]
    }


class PassportViewSet(CanClientDataBeModifiedMixin, ModelViewSet):
    """Паспортные данные клиента."""
    queryset = m.Passport.objects.all()
    serializer_class = s.PassportSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'client')
    custom_serializer_classes = {
        'upload_passport_images': s.UploadPassportPhotosSerializer,
        'upload_passport_images_by_key': s.UploadPassportPhotosSerializer,
    }
    search_fields = ('first_name', 'last_name', 'middle_name')

    @action(methods=('POST',), detail=True, parser_classes=(MultiPartParser,))
    def upload_passport_images(self, request, pk=None, *args, **kwargs):
        """Загрузка фотографий/сканов паспорта"""
        serializer = self.get_serializer(data=request.data)
        passport = self.get_object()
        self._save_passport_data(passport, serializer)
        return Response(status=204)

    @action(methods=('POST',), detail=False, parser_classes=(MultiPartParser,), permission_classes=(AllowAny,),
            url_path=r'by-key/(?P<key>\[a-zA-Z0-9_\-]+)/upload_passport_images', pagination_class=None)
    def upload_passport_images_by_key(self, request, key=None, *args, **kwargs):
        """Загрузка фотографий/сканов паспорта по ссылке из qr-кода"""
        passport = self._get_passport_by_key(key)
        serializer = self.get_serializer(data=request.data)
        self._save_passport_data(passport, serializer)
        return Response(status=204)

    @staticmethod
    def _save_passport_data(passport, serializer):
        serializer.is_valid(raise_exception=True)
        passport.passport_main_photo = serializer.validated_data.get('passport_main_photo', None)
        passport.passport_registry_photo = serializer.validated_data.get('passport_registry_photo', None)
        passport.previous_passport_photo = serializer.validated_data.get('previous_passport_photo', None)
        passport.client_photo = serializer.validated_data.get('client_photo', None)
        passport.save()

    @staticmethod
    def _get_passport_by_key(key):
        try:
            token = m.OrderTempToken.objects.get_token(key=key, type=c.OrderTempTokenType.PASSPORT,
                select_related=('order', 'order__passport'))
        except m.OrderTempToken.TokenIsOutdatedException:
            raise rest_exc.ValidationError(__('Заявка не найдена или срок действия токена завершён'))

        passport = token.order.passport
        # passport = m.Passport.objects.filter(order__ordertemptoken=token).first()
        if not passport:
            raise rest_exc.ValidationError('Паспортные данные не найдены')
        return passport


class PersonalDataViewSet(CanClientDataBeModifiedMixin, ModelViewSet):
    queryset = m.PersonalData.objects.all()
    serializer_class = s.PersonalDataSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'client', 'habitation_location', 'registry_location')
    select_for_includes = {
        '__all__': ['appearance']
    }


class FamilyDataViewSet(CanClientDataBeModifiedMixin, ModelViewSet):
    queryset = m.FamilyData.objects.all()
    serializer_class = s.FamilyDataSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'client', 'marital_status',)


class CareerEducationViewSet(CanClientDataBeModifiedMixin, ModelViewSet):
    queryset = m.CareerEducation.objects.all()
    serializer_class = s.CareerEducationSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'client', 'education', 'workplace_category')


class ExtraDataViewSet(CanClientDataBeModifiedMixin, ModelViewSet):
    queryset = m.ExtraData.objects.all()
    serializer_class = s.ExtraDataSerializer
    permission_classes = (p.OrderFlowAccessPolicy,)
    filterset_fields = ('id', 'order', 'client',)
