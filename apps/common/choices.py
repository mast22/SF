from typing import Tuple


class ChoicesMetaclass(type):
    @classmethod
    def set_attrs(mcs, attrs):
        choices = {}
        for attr_name, value in attrs.items():
            if not attr_name.startswith('_') and not isinstance(value, classmethod):
                if isinstance(value, str):
                    db_value = plural_value = value
                elif len(value) == 2:
                    db_value, plural_value = value
                else:
                    db_value = plural_value = value

                choices[db_value] = plural_value
                attrs[attr_name] = db_value
        attrs['_choices'] = choices
        return attrs

    def __new__(mcs, name, bases, attrs):
        attrs = mcs.set_attrs(attrs)
        return super().__new__(mcs, name, bases, attrs)

    def __iter__(self):
        return self._choices.__iter__()

    def __contains__(self, item):
        return item in self._choices


class Choices(metaclass=ChoicesMetaclass):
    """Базовый класс для констант, применяемых в ENUM-like полях"""
    _choices = {}

    @classmethod
    def as_choices(cls):
        return tuple((k, v) for k, v in cls._choices.items())

    @classmethod
    def keys(cls) -> Tuple:
        return tuple(cls._choices.keys())

    @classmethod
    def plural(cls, item):
        return cls._choices[item]

    @classmethod
    def length(cls):
        assert all(isinstance(k, str) for k in cls.keys()),\
                f'Error with {cls.__name__}: Length is not available for non str choices'
        return max(map(len, cls.keys()))
