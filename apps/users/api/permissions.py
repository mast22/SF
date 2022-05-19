from apps.common.permissions.base import BaseAccessPolicy
from apps.common.permissions import utils as u
from apps.users.const import Roles as R


class BaseUserAccessPolicy(BaseAccessPolicy):
    @staticmethod
    def check_if_wrong_region(self, ch_user, request, view, action, *args, **kwargs) -> bool or None:
        """Проверка, что у юзера есть доступ к изменяемому региону.
        Регион применим только к территориалу, поэтому изменяемый юзер - территориал, иначе выдаст ошибку
        в сериалайзере.
        """
        need_check, creation, new_region = u.make_sure_need_checking(ch_user, field='region')
        if not need_check or ch_user.role != R.TER_MAN:
            return False

        user = request.user
        # 1я итерация - логика на if-else влоб. Будет время - переделаю в более удобную форму.
        result = False
        if user.role == R.ADMIN:
            result = True
        elif user.role == R.ACC_MAN:
            result = new_region.acc_man_id == user.id
        elif user.role == R.TER_MAN:
            result = new_region.id == user.region_id

        return not result

    @staticmethod
    def check_if_wrong_ter_man(self, ch_user, request, view, action, *args, **kwargs) -> bool or None:
        """Проверка, что у юзера есть доступ к изменяемому территориальному менеджеру.
        Территориал применим только к агенту, поэтому изменяемый юзер - агент.
        """
        need_check, creation, new_ter_man = u.make_sure_need_checking(ch_user, field='ter_man')
        if not need_check or ch_user.role != R.AGENT:
            return False

        user = request.user
        # 1я итерация - логика на if-else влоб. Будет время - переделаю в более удобную форму.
        result = False
        if user.role == R.ADMIN:
            result = True
        elif user.role == R.ACC_MAN:
            result = new_ter_man.region.acc_man_id == user.id
        elif user.role == R.TER_MAN:
            result = new_ter_man.id == user.id

        return not result

    @staticmethod
    def check_if_wrong_agent_banks(self, ch_user, request, view, action, *args, **kwargs) -> bool or None:
        """Проверка, что у юзера есть доступ к изменяемым связям с банками.
        Поле agent_banks применимо только к агенту, поэтому изменяемый юзер - агент.
        """
        need_check, creation, new_agent_banks = u.make_sure_need_checking(ch_user, field='agent_banks',
                is_many_to_many=True)
        if not need_check or ch_user.role != R.AGENT:
            return False

        user = request.user
        # 1я итерация - логика на if-else влоб. Будет время - переделаю в более удобную форму.
        result = False
        if user.role == R.ADMIN:
            result = True
        elif user.role == R.ACC_MAN:
            result = all(ag_b.terman_bank.ter_man.region.acc_man_id == user.id for ag_b in new_agent_banks)
        elif user.role == R.TER_MAN:
            result = all(ag_b.terman_bank.ter_man_id == user.id for ag_b in new_agent_banks)

        return not result

    @staticmethod
    def check_if_wrong_managed_regions(self, ch_user, request, view, action, *args, **kwargs) -> bool or None:
        """Проверка, что юзер может быть назначен аккаунт-менеджером на соотв. регионы.
        Применимо только к аккаунт-менеджеру, менять может только админ
        """
        need_check, creation, new_agent_banks = u.make_sure_need_checking(ch_user, field='agent_banks',
                is_many_to_many=True)
        if not need_check or ch_user.role != R.ACC_MAN:
            return False

        return not request.user.role == R.ADMIN



class UserAccessPolicy(BaseUserAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к своим юзерам
            'actions': ('<rest_actions>', 'change_password',),
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к своим агентам
            'actions': ('<rest_actions>', 'change_password',),
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:ter_man',
            'effect': 'allow',
        },
        {
            # Все пользователи - полный доступ к своей учётке.
            'actions': ('<rest_actions>', 'change_password',),
            'roles': '*',
            'queryset_filters': 'filter_is_owner:<self>',
            'effect': 'allow',
        },

        # Проверки полей при добавлении/изменении.
        {
            # Проверка полей при добавлении/изменении пользователя
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': (
                'check_if_wrong_region',
                'check_if_wrong_ter_man',
                'check_if_wrong_agent_banks',
                'check_if_wrong_managed_regions',
            ),
            'effect': 'deny'
        },
    )


class AgentAccessPolicy(BaseUserAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к своим агентам
            'actions': ('<rest_actions>', 'change_password',),
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:ter_man__region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к своим агентам
            'actions': ('<rest_actions>', 'change_password',),
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
        {
            # Агенты - полный доступ к своей учётке.
            'actions': ('<rest_actions>', 'change_password',),
            'roles': '*',
            'queryset_filters': 'filter_is_owner:<self>',
            'effect': 'allow',
        },

        # Проверки полей при добавлении/изменении.
        {
            # Проверка доступности поля ter_man - территориал для данного агента
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': ('check_if_wrong_ter_man', 'check_if_wrong_agent_banks'),
            'effect': 'deny'
        },

    )


class TerManAccessPolicy(BaseUserAccessPolicy):
    role_lookup = 'role'
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
            # Аккаунт менеджер - полный доступ к своим юзерам
            'actions': ('<rest_actions>', 'change_password',),
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:region__acc_man',
            'effect': 'allow',
        },
        {
            # Территориалы - полный доступ к своей учётке
            'actions': ('<rest_actions>', ),
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:<self>',
            'effect': 'allow',
        },
        {
            # Агенты - read-only доступ к своему территориалу
            'actions': ('<safe_methods>', ),
            'roles': R.AGENT,
            'queryset_filters': 'filter_is_owner:agents',
            'effect': 'allow',
        },

        # Проверки полей при добавлении/изменении.
        {
            # Проверка корректности региона
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': 'check_if_wrong_region',
            'effect': 'deny'
        },
    )


class AccManAccessPolicy(BaseUserAccessPolicy):
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
            # Аккаунт менеджер - полный доступ к своей записи
            'actions': ('<rest_actions>', ),
            'roles': R.ACC_MAN,
            'queryset_filters': 'filter_is_owner:<self>',
            'effect': 'allow',
        },
        {
            # Территориалы - доступ на чтение к своему акк. менеджеру
            'actions': '<safe_methods>',
            'roles': R.TER_MAN,
            'queryset_filters': 'filter_is_owner:managed_regions__ter_mans',
            'effect': 'allow',
        },

        # Проверки полей при добавлении/изменении.
        {
            # Проверка корректности региона
            'actions': ('create', 'update', 'partial_update',),
            'type': 'object_level',
            'conditions': 'check_if_wrong_managed_regions',
            'effect': 'deny'
        },
    )


class AdminAccessPolicy(BaseUserAccessPolicy):
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
            # Аккаунт менеджер, территориал - доступ только на чтение
            'actions': '<safe_methods>',
            'roles': (R.ACC_MAN, R.TER_MAN),
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )


class AllowedIpsAccessPolicy(BaseAccessPolicy):
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
            # Аккаунт менеджер - доступ только на чтение к своим записям
            'actions': '<safe_methods>',
            'roles': (R.ACC_MAN, R.TER_MAN),
            'queryset_filters': 'filter_is_owner:user',
            'effect': 'allow',
        },
    )
