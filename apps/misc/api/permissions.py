from apps.common.permissions.base import BaseAccessPolicy
from apps.users.const import Roles as R


class MesaBankAccessPolicy(BaseAccessPolicy):
    rules = (
        # Фильтры
        {
            # Админ, Аккаунт менеджер, территориал -- полный доступ ко всем записям
            'actions': '<rest_actions>',
            'roles': (R.ADMIN, R.ACC_MAN, R.TER_MAN),
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
        {
            # Агенты - доступ на чтение ко всем записям
            'actions': '<safe_methods>',
            'roles': R.AGENT,
            'queryset_filters': 'filter_allow_all',
            'effect': 'allow',
        },
    )
