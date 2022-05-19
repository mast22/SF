from django.utils.translation import gettext_lazy as __
from rest_framework.decorators import action
from rest_framework import exceptions as rest_exc
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from apps.common.viewsets import ModelViewSet
from .. import models as m
from . import serializers as s
from . import permissions as p
from .. import logger


class UserViewSet(ModelViewSet):
    """
    Пользователи.
    В логистике документов производится фильтрация по территориалам filter[role]=ter_man
    """
    queryset = m.User.objects.all()
    serializer_class = s.UserSerializer
    permission_classes = (p.UserAccessPolicy,)
    custom_serializer_classes = {
        'change_password': s.ChangePasswordSerializer
    }
    filterset_fields = ('id', 'role', 'region', 'ter_man', 'status',
        'ter_man__partners', 'region__ter_mans', 'outlets__partner__region__ter_mans')
    search_fields = ('phone', 'first_name', 'last_name', 'middle_name',)
    prefetch_for_includes = {
        '__all__': ['agent_banks', 'agent_banks__agent', 'managed_regions', 'ter_man']
    }

    @swagger_auto_schema(methods=('post',), responses={204: '-No Content-'})
    @action(detail=True, methods=('post',), name=__('Изменить пароль'))
    def change_password(self, request, *args, **kwargs):
        """Изменение пароля пользователя"""
        user = self.get_object()
        serializer = self.get_serializer(instance=user, data=request.data)
        # Сначало проверим что старый пароль совпадает с текущим

        if not user.check_password(serializer.initial_data['old_password']):
            raise rest_exc.ValidationError('Не верный текущий пароль')

        serializer.is_valid(raise_exception=True)

        # Отправлять проверочный код не нужно, но нужно уведомить юзера согласно настройкам.
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        logger.info(f'Password changed by user. User: {user.id} {user}')
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllowedIpsViewSet(ModelViewSet):
    """
    Разрешённые IP-адреса для администратора и аккаунт-менеджера
    """
    queryset = m.AllowedIP.objects.all()
    serializer_class = s.AllowedIPSerializer
    permission_classes = (p.AllowedIpsAccessPolicy,)
    filterset_fields = ['id', 'is_active']

    select_for_includes = {
        '__all__': ['user'],
    }



class AgentViewSet(ModelViewSet):
    """Агенты."""
    queryset = m.Agent.objects.all()
    serializer_class = s.AgentSerializer
    permission_classes = (p.AgentAccessPolicy,)
    filterset_fields = ('id', 'status', 'ter_man__region', 'ter_man', 'ter_man__partners', 'ter_man__partners__outlets')
    search_fields = ('phone', 'first_name', 'last_name', 'middle_name',)
    prefetch_for_includes = {
        '__all__': ['agent_banks','agent_banks', 'ter_man']
    }


class TerManViewSet(ModelViewSet):
    """Территориальные менеджеры."""
    queryset = m.TerMan.objects.all()
    serializer_class = s.TerManSerializer
    permission_classes = (p.TerManAccessPolicy,)
    filterset_fields = ('id', 'status', 'region', 'partners', 'partners__outlets', 'agents')
    search_fields = ('phone', 'first_name', 'last_name', 'middle_name',)


class AccManViewSet(ModelViewSet):
    """Аккаунт-менеджеры."""
    queryset = m.AccMan.objects.all()
    serializer_class = s.AccManSerializer
    permission_classes = (p.AccManAccessPolicy,)
    filterset_fields = ('id', 'status', 'managed_regions', 'managed_regions__ter_mans')
    search_fields = ('phone', 'first_name', 'last_name', 'middle_name',)


class AdminViewSet(ModelViewSet):
    """Администраторы"""
    queryset = m.Admin.objects.all()
    serializer_class = s.UserSerializer
    permission_classes = (p.AdminAccessPolicy,)
    filterset_fields = ('id', 'status',)
    search_fields = ('phone', 'first_name', 'last_name', 'middle_name',)


# from rest_framework.response import Response
# from apps.common.viewsets import ReadOnlyModelViewSet
# from rest_framework import status
# from rest_framework.decorators import action
#
#
# class CommissionReportViewSet(ReadOnlyModelViewSet):
#     """Отчёт о сумме, заработанной за период"""
#     serializer_class = s.CommissionReportSummarySerializer
#
#     def get_queryset(self):
#         q = m.User.objects.all()
#         return q
#
#     def list(self, agent_pk=None, *args, **kwargs):
#         """Суммарный отчёт по комиссии агентов, по банкам."""
#         data = {}
#         return Response(data=data, status=status.HTTP_200_OK)
#
#     def retrieve(self, agent_pk=None, pk=None, *args, **kwargs):
#         """Суммарный отчёт по комиссии агента для заданного банка."""
#         data = {}
#         return Response(data=data, status=status.HTTP_200_OK)
#
#     @action(methods=('get',), detail=True)
#     def credit_products(self, pk=None, *args, **kwargs):
#         """Суммарный отчёт по комиссиям агента для заданного банка по кредитным продуктам."""
#         data = {}
#         return Response(data=data, status=status.HTTP_200_OK)
#
#     @action(methods=('get',), detail=True)
#     def extra_services(self, pk=None, *args, **kwargs):
#         """Суммарный отчёт по комиссиям агента для заданного банка по доп. услугам"""
#         data = {}
#         return Response(data=data, status=status.HTTP_200_OK)
