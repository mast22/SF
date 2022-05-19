from collections import namedtuple


# HTTP-Методы, которые не меняют данные.
SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS',)


# Структуры для кастомного метода
UserMethodTuple = namedtuple('CustomMethod', ('name', 'args', 'kwargs'))

# Нормализованная структура кастомного метода (queryset_filters, conditions)
NormalizedMethodTuple = namedtuple('NormalizedMethodTuple', ('method', 'args', 'kwargs'))
