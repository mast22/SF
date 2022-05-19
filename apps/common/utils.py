import secrets
import string
import uuid
from datetime import date, datetime
from importlib import import_module
from itertools import chain
from typing import Union

from django.conf import settings
from django.utils import timezone as tz


def generate_random_token(length, urlsafe=True):
    """
    Генерирует случайный токен заданной длины.
    Если задан параметр urlsafe, возвращается url-encoded строка."""
    if urlsafe:
        return secrets.token_urlsafe(int(length * 0.75))
    else:
        return secrets.token_bytes(length)


def generate_random_uuid():
    return str(uuid.uuid4())


def generate_code(size=4, chars=string.digits) -> str:
    """Генерирует уникальный проверочный код длины size из символов chars (по умолчанию цифры 0-9)"""
    return ''.join(secrets.choice(chars) for _ in range(size))


def xor(a, b):
    return bool(a) != bool(b)


def nested_getattr(object, lookup: str):
    for level in lookup.split('.'):
        object = getattr(object, level)

    return object


def compose_full_name(last_name, first_name, middle_name=None):
    return ' '.join(n for n in (last_name, first_name, middle_name) if n is not None)


def string_to_boolean(string: str) -> bool:
    """Конвертирует строковое представление boolean-значения в bool"""
    if type(string) != str:
        return bool(string)
    string = string.lower().strip()
    if string in ('true', '1', 't', 'y', 'yes'):
        return True
    elif string in ('false', '0', 'f', 'n', 'no', ''):
        return False
    raise ValueError(f'Value "{string}" can\'t be converted to boolean')


def import_from_string(callable_path: str):
    """
    Пытается загрузить класс или метод, переданные в виде строки
    Взято: rest_framework/settings.py
    """
    parts = callable_path.split('.')
    module_path, callable_name = '.'.join(parts[:-1]), parts[-1]
    return import_from_module(module_path, callable_name)


def import_from_module(module_path: str, callable_name: str):
    try:
        # Nod to tastypie's use of importlib.
        module = import_module(module_path)
        return getattr(module, callable_name)
    except ImportError as err:
        msg = 'Could not import "{0}" for setting. {1}: {2}.'.format(module_path, err.__class__.__name__, err)
        raise ImportError(msg)


def try_to_convert_to_int(value):
    try:
        value = int(value)
        return True, value
    except (KeyError, ValueError, TypeError):
        return False, value


def convert_pk_to_integer(pk):
    result, pk_int = try_to_convert_to_int(pk)
    if not result:
        from rest_framework.exceptions import ValidationError
        raise ValidationError('Primary key is not integer')
    return pk_int


def get_related_pk(pk_name=None, request_pk_name=None, view=None, is_json_api=True):
    assert view is not None, f'get_related_pk got wrong parameters! view or  '
    pk = view.kwargs.get(pk_name, None)
    if pk:
        pk = convert_pk_to_integer(pk)
    elif request_pk_name and view.request:
        pk = get_filter_value(request_pk_name, view.request, is_json_api)
        if pk:
            pk = convert_pk_to_integer(pk)
    return pk


def get_filter_value(key, request, is_json_api=True, default=None):
    if is_json_api:
        key = f'filter[{key}]'
    value = default
    if request:
        value = request.query_params.get(key, default)
    return value


def get_current_month():
    now = tz.now()
    return datetime(year=now.year, month=now.month, day=1, hour=0, minute=0, second=0)


def datetime_as_day(user_datetime=None):
    """Возвращает datetime: полночь текущего дня с учётом timezone"""
    if user_datetime:
        day = user_datetime.date()
    else:
        day = date.today()
    cur_day = datetime.combine(day, datetime.min.time())
    return enforce_timezone(cur_day)


def enforce_timezone(value: tz.datetime, cur_tz: tz.timezone=None):
    """
    When `self.default_timezone` is `None`, always return naive datetimes.
    When `self.default_timezone` is not `None`, always return aware datetimes.
    """
    if not cur_tz:
        cur_tz = tz.get_current_timezone() if settings.USE_TZ else None

    if cur_tz is not None:
        if tz.is_aware(value):
            return value.astimezone(cur_tz)
        return tz.make_aware(value, cur_tz)
    elif (cur_tz is None) and tz.is_aware(value):
        return tz.make_naive(value, tz.utc)
    return value


def get_person_age(birthdate: date, current_datetime: date):
    years_have_passed = current_datetime.year - birthdate.year
    if birthdate.month < current_datetime.month:
        # День рождения уже был в этом году
        return years_have_passed
    elif birthdate.month == current_datetime.month:
        if birthdate.day <= current_datetime.day:
            # День рождения был в этом месяце или сегодня
            return years_have_passed
        return years_have_passed - 1
    return years_have_passed - 1


def is_iterable(obj) -> bool:
    """Проверяет, что объект ялвяется Iterable, но не строкой"""
    if isinstance(obj, str):
        return False
    try:
        iter(obj)
    except TypeError:
        return False
    return True


def model_to_dict(instance, fields=None, exclude=None):
    """
    Return a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    """
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)
    return data


def value_or_zero(value: Union[float, int, None]):
    return 0 if value is None else value


def instance_of_in(klass, list):
    for item in list:
        if isinstance(item, klass):
            return True

    return False