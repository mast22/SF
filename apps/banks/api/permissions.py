from apps.common.permissions.base import BaseAccessPolicy
from apps.users.const import Roles as R


class BankAccessPolicy(BaseAccessPolicy):
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
            # Все остальные - read-only доступ ко всем записям
            'actions': '<safe_methods>',
            'roles': (R.ACC_MAN, R.TER_MAN, R.AGENT),
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )


class TerManBankAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к территориалам своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - доступ на чтение к своим записям
            'actions': '<safe_methods>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:ter_man',
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
        'ter_man': {
            R.ACC_MAN: 'region__acc_man_id',
        },
    }



class TerManCreditProductAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к территориалам своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:terman_bank__ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - доступ на чтение к своим записям
            'actions': '<safe_methods>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:terman_bank__ter_man',
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
        'terman_bank': {
            R.ACC_MAN: 'ter_man__region__acc_man_id',
        },
    }



class AgentBankAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к настройкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:agent__ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к настройкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:agent__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к своим настройкам
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
            R.TER_MAN: 'ter_man_id',
        },
        'terman_bank': {
            R.ACC_MAN: 'ter_man__region__acc_man_id',
            R.TER_MAN: 'ter_man_id'
        },
    }


class AgentCreditProductAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к настройкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:terman_credit_product__terman_bank__ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к настройкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:terman_credit_product__terman_bank__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к своим настройкам
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
        'agent_bank': {
            R.ACC_MAN: 'agent__ter_man__region__acc_man_id',
            R.TER_MAN: 'agent__ter_man_id',
        },
        'terman_credit_product': {
            R.ACC_MAN: 'ter_man_bank__ter_man__region__acc_man_id',
            R.TER_MAN: 'ter_man_bank__ter_man_id',
        },
    }


class AgentExtraServicesAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к настройкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:terman_extra_service__terman_bank__ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к настройкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:terman_extra_service__terman_bank__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к своим настройкам
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:agent_bank__agent',
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
        'agent_bank': {
            R.ACC_MAN: 'agent__ter_man__region__acc_man_id',
            R.TER_MAN: 'agent__ter_man_id',
        },
        'terman_extra_service': {
            R.ACC_MAN: 'ter_man_bank__ter_man__region__acc_man_id',
            R.TER_MAN: 'ter_man_bank__ter_man_id',
        },
    }



class OrderChoosableCreditProductsAccessPolicy(BaseAccessPolicy):
    rules = (
        # Фильтры
        {
            # Все остальные - read-only доступ ко всем записям
            'actions': '<safe_methods>',
            'roles': '*',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )


class OutletBankAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к настройкам торговых точек в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к настройкам торговых точек своих партнёров
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:outlet__partner__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к настройкам торговых точек, разрешение через OutletAgent
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:outlet__outlet_agent__agent',
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
        'outlet': {
            R.ACC_MAN: 'partner__region__acc_man_id',
            R.TER_MAN: 'partner__ter_man_id',
        },
    }


class OutletCreditProductsAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к настройкам торговых точек в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:outlet_bank__outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к настройкам торговых точек своих партнёров
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:outlet_bank__outlet__partner__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение к настройкам торговых точек, разрешение через OutletAgent
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:outlet_bank__outlet__outlet_agent__agent',
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
        'outlet_bank': {
            R.ACC_MAN: 'outlet__partner__region__acc_man_id',
            R.TER_MAN: 'outlet__partner__ter_man_id',
        },
    }

