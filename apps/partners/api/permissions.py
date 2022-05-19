from apps.common.permissions.base import BaseAccessPolicy
from apps.common.permissions import utils as u
from apps.users.const import Roles as R


class RegionAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к своим регионам
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - доступ только на чтение к своему региону
            'actions': '<safe_methods>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:ter_mans',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к своему региону
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:ter_mans__agents',
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
        'acc_man': {
            R.ACC_MAN: 'id',
        },
    }


class PartnerAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к партнёрам в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к своим партнёрам
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к партнёрам своего территориала
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:ter_man__agents',
            'effect': 'allow',
        },

        # # Проверки полей при добавлении/изменении.
        # {
        #     'actions': ('create', 'update', 'partial_update',),
        #     'type': 'object_level',
        #     'conditions': ('check_if_wrong_ter_man', 'check_if_wrong_region'),
        #     'effect': 'deny'
        # },
        # Проверки полей при добавлении/изменении.
        {
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': 'check_for_wrong_fields',
            'effect': 'deny'
        },
    )
    fields_to_check = {
        'ter_man': {
            R.ACC_MAN: 'region__acc_man_id',
            R.TER_MAN: 'id'
        },
        'region': {
            R.ACC_MAN: 'acc_man_id',
            R.TER_MAN: ('ter_mans', 'id'),
        }
    }


class OutletAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к торговым точкам в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к своим партнёрам
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:partner__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к своим торговым точкам.
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:agents',
            'effect': 'allow',
        },

        # # Проверки полей при добавлении/изменении.
        # {
        #     'actions': ('create', 'update', 'partial_update',),
        #     'type': 'object_level',
        #     'conditions': (
        #         'check_if_wrong_region',
        #         'check_if_wrong_partner',
        #         'check_if_wrong_agents',
        #     ),
        #     'effect': 'deny'
        # },
        # Проверки полей при добавлении/изменении.
        {
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': 'check_for_wrong_fields',
            'effect': 'deny'
        },
    )
    fields_to_check = {
        'partner': {
            R.ACC_MAN: 'partner__region__acc_man_id',
            R.TER_MAN: 'ter_man_id'
        },
        'agents:is_many_to_many': {
            R.ACC_MAN: 'ter_man__region__acc_man_id',
            R.TER_MAN: 'ter_man_id'
        },
    }

    @staticmethod
    def check_if_wrong_agents(self, outlet, request, view, action, *args, **kwargs) -> bool or None:
        """Проверка, что назначен правильный регион"""
        need_check, creation, new_agents = u.make_sure_need_checking(outlet, field='agents', is_many_to_many=True)
        if not need_check:
            return False

        user = request.user
        result = False
        if user.role == R.ADMIN:
            result = True
        elif user.role == R.ACC_MAN:
            result = all(agent.ter_man.region.acc_man == user.id for agent in new_agents)
        elif user.role == R.TER_MAN:
            result = all(agent.ter_man == user.id for agent in new_agents)

        return not result


class OutletAgentAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к агентам-торговым точкам в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к своим агентам-торговым точкам
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:outlet__partner__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к своим торговым точкам.
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:agent',
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
        'agent': {
            R.ACC_MAN: 'ter_man__region__acc_man_id',
            R.TER_MAN: 'ter_man_id'
        },
        'outlet': {
            R.ACC_MAN: '',
            R.TER_MAN: '',
        }
    }



class LocationAccessPolicy(BaseAccessPolicy):
    rules = (
        # Фильтры
        {
            # Полный доступ ко всем записям всем пользователям, т.к. нужен всем, включая агента.
            'actions': '*',
            'roles': '*',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )



class PartnerBankAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к связке партнёр-банк в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к связке партнёр-банк в своих регионах
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:partner__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к связке партнёр-банк в своих регионах
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:partner__ter_man__agents',
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
        'partner': {
            R.ACC_MAN: 'region__acc_man_id',
            R.TER_MAN: 'ter_man_id'
        },
    }
