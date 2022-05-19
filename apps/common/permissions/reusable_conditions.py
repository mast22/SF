"""Типовые функции для проверки прав"""
from django.db.models import QuerySet
from apps.common.utils import is_iterable
from . import utils as u
from apps.users.const import Roles


def filter_allow_all(perm_obj, queryset, request, view, action, *args, **kwargs) -> QuerySet:
    return queryset


def filter_deny_all(perm_obj, queryset, request, view, action, *args, **kwargs) -> QuerySet:
    return queryset.none()


def filter_is_owner(perm_obj, queryset, request, view, action, *args, **kwargs) -> QuerySet:
    user = request.user
    owner_lookup = u.get_arg(args, kwargs, 0, 'owner_lookup', default='user')
    owner_lookup = 'id' if owner_lookup == '<self>' else f'{owner_lookup}__id'
    queryset = queryset.filter(**{owner_lookup: user.id})
    return queryset


def check_for_wrong_fields(perm_obj, instance, request, view, action, *args, **kwargs) -> bool or None:
    """Проверка, что назначен правильный related_field.
    Необходимо задать у permissions-класса аттрибут fields_to_check.

    Пример:
    fields_to_check = {
        'ter_man': {  # Проверяемый related-field (instance.ter_man)
            R.ACC_MAN: 'region__acc_man_id',
                # Для акк-менеджера проверям instance.region.acc_man_id == cur_user.id
            R.TER_MAN: 'id'
        },
        'region': {  # Проверяемый related-field (instance.region)
            R.ACC_MAN: 'acc_man_id',
            R.TER_MAN: ('ter_mans', 'id'),
                # Для территориала проверям instance.region.ter_mans.filter(id=cur_user.id).exists()
                # Список из 2х значений нужен, если проходим через many-to-many связь до текущего юзера
                # 1й аргумент - lookup с "." - путь до m-m аттрибута
                # 2й аргумент - lookup с "." - путь от m-m аттрибута до id текущего юзера.
        }
    }
    """
    fields_to_check = getattr(perm_obj, 'fields_to_check', None)
    if fields_to_check is None:
        raise AttributeError(f'You need to set "fields_to_check" attribute on {perm_obj.__class__}')

    for field, roles in fields_to_check.items():
        field_list = field.split(':')
        flags = {'is_many_to_many': False,}
        field_name = field_list[0]
        if len(field_list) > 0:
            for flag in field_list[1:]:
                if flag in flags:
                    flags[flag] = True
        result = check_exact_field(field_name, roles, flags, instance, request, view, action)
        if not result:
            # True = Deny, False = Allow, т.к. используется с effect="deny"!
            if perm_obj.print_log:
                print(f'check_for_wrong_fields. Field: {field} is wrong! roles: {roles}')
            return True
    return False


def check_exact_field(field: str, roles: dict, flags: dict, instance, request, view, action):
    """Проверка конкретного related_field на допустимые значения"""
    is_many_to_many = flags.get('is_many_to_many', False)
    need_check, creation, new_rel_instance = u.make_sure_need_checking(instance, field, is_many_to_many)
    if not need_check:
        return True

    user = request.user
    if user.role == Roles.ADMIN:
        # Админу разрешаем изменять все записи.
        return True

    cur_role_id_lookup = roles.get(user.role, None)
    if cur_role_id_lookup is None:
        return False
    elif is_iterable(cur_role_id_lookup):
        user_id_items, user_mm_lookup = cur_role_id_lookup
        user_id_items = user_id_items.split('__')
    else:
        user_id_items = cur_role_id_lookup.split('__')
        user_mm_lookup = None

    # TODO: Учесть many-to-many fields
    related_instance = getattr(instance, field)
    if is_many_to_many:
        result = all(_check_related_field(user, new_rel_instance, cur_related_instance,
                    user_id_items, user_mm_lookup)
                for cur_related_instance in related_instance)
    else:
        result = _check_related_field(user, new_rel_instance, related_instance, user_id_items, user_mm_lookup)

    return result


def _check_related_field(user, new_rel_instance, related_instance, user_id_items, user_mm_lookup):
    # Check existed field:
    cur_related_instance = related_instance
    for attr in user_id_items:
        cur_related_instance = getattr(cur_related_instance, attr)

    if user_mm_lookup is not None:
        result = cur_related_instance.filter(**{user_mm_lookup:user.id}).exists()
    else:
        result = cur_related_instance == user.id

    if not result:
        return False

    # Check new field:
    related_field = new_rel_instance
    for attr in user_id_items:
        related_field = getattr(related_field, attr)

    if user_mm_lookup is not None:
        result = related_field.filter(**{user_mm_lookup:user.id}).exists()
    else:
        result = related_field == user.id

    return result
