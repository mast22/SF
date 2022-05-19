from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as __, gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import CreateListRetrieveModelViewSet, ModelViewSet
from apps.msgs.shortcuts import send_auth_code
from apps.orders import const as c, models as m
from apps.orders.api import serializers as s
from apps.users.models import TempToken



class ClientsViewSet(CreateListRetrieveModelViewSet):
    """ Клиенты
    Поскольку номера телефонов клиентов могут повторяться для
    обеспечения уникальности был добавлен read_only параметр sequence
    Символ "+" в GET параметрах необходимо кодировать как "%2B"

    Создавать пользователя необходимо только после подтверждения номера телефона
    """
    queryset = m.Client.objects.all()
    serializer_class = s.ClientSerializer
    filterset_fields = ('id', 'phone', 'created_at',)
    search_fields = ('passport__first_name', 'passport__last_name', 'passport__middle_name')

    custom_serializer_classes = {
        'send_code': s.ClientSendCodeSerializer,
        'check_code': s.ClientCheckCodeSerializer,
    }
    prefetch_for_includes = {
        '__all__': ('personal_data', 'passport'),
    }

    @swagger_auto_schema(method='post', responses={202: s.ClientSendCodeRespSerializer})
    @action(detail=False, methods=('POST',), name=__('Отправить проверочный код'))
    def send_code(self, request, *args, **kwargs):
        """Отправляет проверочный код на телефон клиента."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_phone = serializer.validated_data['phone']
        temp_token = TempToken.create_for_client(phone=client_phone)

        # TODO: Удалить, когда починю dramatiq-таски и коды будут падать в DummyMessages!
        temp_token.code = '1234'
        temp_token.save()

        send_auth_code(temp_token)
        data = s.ClientSendCodeRespSerializer(dict(
            detail=_('Код подтверждения успешно отправлен'),
            temp_token=temp_token.key,
            expires=temp_token.moment_end,
            repeat=temp_token.can_repeat_at,
            now=tz.now(),
        )).data
        return Response(data, status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(method='post', responses={201: s.ClientSerializer})
    @action(detail=False, methods=('POST',), name=__('Проверить проверочный код'))
    def check_code(self, request, *args, **kwargs):
        """Проверяет проверочный код, в случае успеха, создаёт нового клиента."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        temp_token = serializer.validated_data['temp_token']
        client = m.Client.objects.create(phone=temp_token.phone)
        data = s.ClientSerializer(client).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)



class ClientOrderViewSet(ModelViewSet):
    """Клиент, привязанный к заявке."""
    queryset = m.ClientOrder.objects
    serializer_class = s.ClientOrderSerializer
    filterset_fields = ('id', 'phone', 'order', 'client')
