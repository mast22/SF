from django.db.models import Q
from typing import Sequence, Mapping



def filter_by_related_field(user, by_field, recursion_field=None,
                query_string='groups__user__id', recursion_limit=2):
    """
    Добавляет фильтрацию по Foreign-полям.
    :param user:
    :param by_field:
    :param recursion_field:
    :param query_string:
    :param recursion_limit:
    :return:
    """
    query_string = '{0}__{1}'.format(by_field, query_string)
    query = Q(**{query_string: user.id})

    if not recursion_field:
        recursion_field = by_field

    for i in range(0, recursion_limit - 1):
        query_string = '{0}__{1}'.format(recursion_field, query_string)
        query |= Q(**{query_string: user.id})
    return query


def make_sure_need_checking(obj, field, is_many_to_many=False, field_comparator=None):
    """
    Убеждаемся, что поле объекта было изменено и требуется дальнейшая проверка прав доступа.
    :param obj: добавленный/изменённый инстанс модели.
    :param field: проверяемое поле.
    :param is_many_to_many: является ли field many-to-many зависимостью
    :param field_comparator: специальный метод для сравнения нового значения с имеющимся в БД.
    :return: need_check, creation, new_field_value
    Необходима ли проверка: bool, Инстанс создаётся (если False - редактируется):bool, изменённое значение field
    """
    need_check = True
    creation = None
    new_field_value = None

    # Пометка в объекте пропустить проверку изменилось ли поле путём сравнения с прошлым значением.
    skip_need_check = getattr(obj, '_validated_data_skip_check', False)

    if not (obj and (hasattr(obj, '_validated_data') or hasattr(obj, '_validated_data_many_to_many'))):
        need_check = False
    else:
        creation = not obj.id
        if creation:
            if is_many_to_many:
                new_field_value = set(obj._validated_data_many_to_many.get(field, set()))
            else:
                new_field_value = getattr(obj, field)
        else:
            # Check if field was changed
            if is_many_to_many:
                if field in obj._validated_data_many_to_many:
                    new_field_value = set(obj._validated_data_many_to_many.get(field, None))
                    if not skip_need_check:
                        old_field_value = getattr(obj, field)
                        old_field_value = set(old_field_value.all()) if old_field_value else set()
                        if new_field_value == old_field_value:
                            need_check = False
                else:
                    need_check = False
            else:
                if field in obj._validated_data:
                    new_field_value = obj._validated_data[field]
                    prev_field_value = getattr(obj, field)
                    if not skip_need_check:
                        fields_equal = field_comparator(prev_field_value, new_field_value, obj) \
                            if field_comparator is not None \
                            else (new_field_value == prev_field_value)
                        if fields_equal:
                            need_check = False
                else:
                    need_check = False
    return need_check, creation, new_field_value


def get_arg(args: Sequence=None, kwargs: Mapping=None,
                position: int=0, name: str=None, default=None):
    """Вспомогательная функция для получения кастомных настроек из args/kwargs"""
    if args and len(args) > position:
        return args[position]
    elif kwargs and name:
        return kwargs.get(name, default)
    else:
        return default


def get_attr(obj, org_field_lookup: str, error_msg: str="Object {obj} doesn't have an organization field: {field}"):
    """Вспомогательная функция для получения вложенного аттрибута по lookup"""
    related_fields = org_field_lookup.split('__')
    related_obj = obj
    for related_field in related_fields:
        related_obj = getattr(related_obj, related_field)
        if not related_obj:
            raise ValueError(error_msg.format(obj=related_obj, field=related_field))
    return related_obj


