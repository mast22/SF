from django.utils.translation import gettext_lazy as __
from rest_framework.permissions import BasePermission
from .base import BaseAccessPolicy


class IsAnonymous(BasePermission):
    """
    Allows access only to not authenticated users.
    """
    message = __('Данный метод доступен только неавторизованным пользователям')
    def has_permission(self, request, view):
        return bool(not request.user or request.user.is_anonymous)


class IsAuthenticated(BasePermission):
    """Allow access only to authenticated users."""
    message = __('Данный метод доступен только авторизованным пользователям')
    def has_permission(self, request, view):
        return bool(request.user and not request.user.is_anonymous)


class CanViewAllAccessPolicy(BaseAccessPolicy):
    """Доступ на просмотр всем, включая неавторизованных пользователей. Изменять может только суперпользователь."""
    allow_anonymous_access = True
    rules = (
        {
            # Пользователь с правами (CRUD)_{object} имеет соотв. доступ на (CRUD) к любому объекту.
            'actions': '<rest_actions>',
            'permissions': '<by_http_method>',
            'object_permissions': '<by_http_method>',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
        {
            'actions': '<safe_methods>',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )


class DefaultAccessPolicy(BaseAccessPolicy):
    # Типовой набор прав:
    rules = (
        {
            # Пользователь с правами (CRUD)_{object} имеет соотв. доступ на (CRUD) к любому объекту.
            'actions': '<rest_actions>',
            'permissions': '<by_http_method>',
            'object_permissions': '<by_http_method>',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
        {
            # Явно запрещаю доступ неавторизованным пользователям (не обязательно)
            'actions': '*',
            'principal': '<is_anonymous>',
            'effect': 'deny',
        },

    )


