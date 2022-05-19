from django.utils.translation import gettext_lazy as __
from django.db import models as dj_m
from rest_framework import status, exceptions as rest_exc
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.common.viewsets import ModelViewSet, ReadOnlyModelViewSet
from apps.orders import models as m, const as c
from apps.orders.api import serializers as s


class ContractViewSet(ModelViewSet):
    queryset = m.Contract.objects.all()
    serializer_class = s.ContractSerializer
    filterset_fields = ('id', 'status', 'order', 'delivery', 'order__outlet', 'order__agent', 'order__agent__ter_man')
    search_fields = (
        'number',
        'order__client_order__phone',
        'order__passport__first_name',
        'order__passport__last_name',
        'order__passport__middle_name',
    )
    custom_serializer_classes = {
        'change_status_by_key': s.ContractStatusSerializer
    }

    prefetch_for_includes = {
        '__all__': ['delivery'],
        'order': ['delivery', 'order'],
    }

    @staticmethod
    def aggregated_stats(qs):
        return qs.aggregate(
            outlet_count=dj_m.Count('status', filter=dj_m.Q(status='outlet')),
            sent_count=dj_m.Count('status', filter=dj_m.Q(status='sent')),
            office_count=dj_m.Count('status', filter=dj_m.Q(status='office')),
            cdek_count=dj_m.Count('status', filter=dj_m.Q(status='cdek')),
            bank_count=dj_m.Count('status', filter=dj_m.Q(status='bank')),
        )


    @action(methods=('POST',), detail=False, url_path=r'by-key/(?P<key>\[a-zA-Z0-9_\-]+)/change_status',
            pagination_class=None)
    def change_status_by_key(self, request, key=None, *args, **kwargs):
        """Изменить статус договора по qr-коду"""
        contract = self._get_contract_by_key(key)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._set_contract_status(contract, serializer)
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _get_contract_by_key(key):
        try:
            token = m.OrderTempToken.objects.get_token(key=key, type=c.OrderTempTokenType.DOCUMENT,
                                                       select_related=('order', 'order__contract'))
        except m.OrderTempToken.TokenIsOutdatedException:
            raise rest_exc.ValidationError(__('Заявка не найдена или срок действия токена завершён'))

        contract = token.order.contract
        # contract = m.Contract.objects.filter(order__ordertemptoken=token).first()
        if not contract:
            raise rest_exc.ValidationError('Договор не найден')
        return contract

    @staticmethod
    def _set_contract_status(contract, serializer):
        status = serializer.validated_data['status']
        contract.status = status
        contract.save(update_fields=('status', 'changed_at'))
        return contract


class DocumentsToSignViewSet(ReadOnlyModelViewSet):
    """Печатные формы для подписания клиентом."""
    queryset = m.DocumentToSign.objects.all()
    serializer_class = s.DocumentToSignSerializer
    filterset_fields = ('id', 'order',)


class DocumentsSignedViewSet(ReadOnlyModelViewSet):
    """Подписанные клиентом документы."""
    queryset = m.DocumentSigned.objects.all()
    serializer_class = s.DocumentSignedSerializer
    filterset_fields = ('id', 'order',)

    @action(detail=False, methods=('POST',), parser_classes=(MultiPartParser,))
    def create_multipart(self, request, *args, **kwargs):
        """Метод для загрузки сканов договоров"""
        serializer = s.DocumentSignedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        if document:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
