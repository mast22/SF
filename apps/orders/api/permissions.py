from apps.common.permissions.base import BaseAccessPolicy
from apps.users.const import Roles as R


# Методы и actions, доступные агенту.
order_actions_agent = (
    'metadata',
    'list',
    'retrieve',
    'create',
    'update',
    'partial_update',
    'telegram_order',
    'send_to_scoring',
    'send_to_authorization',
    'send_client_refused',
    'choose_credit_product',
    'send_documents',
    'get_upload_passport_qrcode',
    'reset_status_to_new',
    'clone_order',
)
# Actions, доступные территориалу/аккаунт-менеджеру.
order_actions_ter_man = (
    'get_contract_qrcode',
)


class OrderAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к заявкам в своих регионах
            'actions': order_actions_agent + order_actions_ter_man,
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к заявкам своих агентов
            'actions': order_actions_agent + order_actions_ter_man,
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:agent__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - полный доступ к своим заявкам
            'actions': order_actions_agent,
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
            R.AGENT: 'id',
        },
        'outlet': {
            R.ACC_MAN: 'partner__region__acc_man_id',
            R.TER_MAN: ('partner__region__ter_mans', 'id'),
            R.AGENT: ('outlet_agents', 'agent_id'),
        },
    }


class TelegramOrderAccessPolicy(BaseAccessPolicy):
    rules = (
        # Фильтры
        {
            # Доступ на чтение ко всем записям всем авторизованным пользователям
            'actions': '<safe_methods>',
            'roles': '*',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )


class GoodAccessPolicy(BaseAccessPolicy):
    rules = (
        # Фильтры
        {
            # Полный доступ ко всем записям всем авторизованным пользователям
            'actions': '<rest_actions>',
            'roles': '*',
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )


class OrderGoodServiceAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к заявкам в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:order_good__order__outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к заявкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:order_good__order__agent__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - полный доступ к своим заявкам
            'actions': '<rest_actions>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:order_good__order__agent',
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
        'order': {
            R.ACC_MAN: 'order_good__order__outlet__partner__region__acc_man_id',
            R.TER_MAN: 'order_good__order__outlet__partner__ter_man_id',
            R.AGENT: 'order_good__order__agent_id',
        },
    }


class OrderFlowAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к заявкам в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:order__outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к заявкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:order__agent__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - полный доступ к своим заявкам
            'actions': '<rest_actions>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:order__agent',
            'effect': 'allow',
        },
        # Проверки полей при добавлении/изменении.
        {
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': 'check_for_wrong_fields',
            'effect': 'deny'
        },
        {
            'actions': ('upload_passport_images', 'upload_passport_images_by_key',),
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:order__agent',
            'effect': 'allow',
        }
    )

    fields_to_check = {
        'order': {
            R.ACC_MAN: 'outlet__partner__region__acc_man_id',
            R.TER_MAN: 'outlet__partner__ter_man_id',
            R.AGENT: 'agent_id',
        },
    }


class OrderExtraServiceAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к заявкам в своих регионах
            'actions': '<rest_actions>',
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:order_credit_product__order__outlet__partner__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к заявкам своих агентов
            'actions': '<rest_actions>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:order_credit_product__order__agent__ter_man',
            'effect': 'allow',
        },
        {
            # Агенты - полный доступ к своим заявкам
            'actions': '<rest_actions>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:order_credit_product__order__agent',
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
        'order_credit_product': {
            R.ACC_MAN: 'order__outlet__partner__region__acc_man_id',
            R.TER_MAN: 'order__outlet__partner__ter_man_id',
            R.AGENT: 'order__agent_id',
        },
    }
