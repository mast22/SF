from apps.common.permissions.base import BaseAccessPolicy
from apps.users.const import Roles as R


class DeliveryAccessPolicy(BaseAccessPolicy):
    rules = (
        # Фильтры
        {
            # Админ - полный доступ ко всем записям
            'actions': '*',
            'roles': R.ADMIN,
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
        {
            # Аккаунт менеджер - полный доступ по своим регионам
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:contracts__order__outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ по заказам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:contracts__order__agent__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение по своим заявкам
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:contracts__order__agent',
            'effect': 'allow',
        },

        # Проверки полей при добавлении/изменении.
        {
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': 'check_for_wrong_fields',
            'effect': 'deny'
        },
    )
    fields_to_check = {
        'contracts:is_many_to_many': {
            R.ACC_MAN: '*',
            R.TER_MAN: 'order__agent__ter_man',
        },
    }
