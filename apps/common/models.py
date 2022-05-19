from typing import Optional, List

from django.db import models as m
from .utils import generate_random_token
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as __


@m.fields.Field.register_lookup
class NotEqual(m.Lookup):
    """Not Equal lookup"""
    lookup_name = 'not'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return '%s <> %s' % (lhs, rhs), params


@m.fields.Field.register_lookup
class NotIn(m.lookups.In):
    """Not Equal lookup"""
    lookup_name = 'not_in'

    def get_rhs_op(self, connection, rhs):
        return 'NOT IN (%s)' % rhs

    def split_parameter_list_as_sql(self, compiler, connection):
        # This is a special case for databases which limit the number of
        # elements which can appear in an 'IN' clause.
        max_in_list_size = connection.ops.max_in_list_size()
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.batch_process_rhs(compiler, connection)
        in_clause_elements = ['(']
        params = []
        for offset in range(0, len(rhs_params), max_in_list_size):
            if offset > 0:
                in_clause_elements.append(' OR ')
            in_clause_elements.append('%s NOT IN (' % lhs)
            params.extend(lhs_params)
            sqls = rhs[offset: offset + max_in_list_size]
            sqls_params = rhs_params[offset: offset + max_in_list_size]
            param_group = ', '.join(sqls)
            in_clause_elements.append(param_group)
            in_clause_elements.append(')')
            params.extend(sqls_params)
        in_clause_elements.append(')')
        return ''.join(in_clause_elements), params


class Model(m.Model):
    """Базовый класс, в котором pk=BigAutoField"""
    id = m.BigAutoField(primary_key=True, blank=True)

    class Meta:
        abstract = True


class BaseTokenManager(m.Manager):
    def get_token(self, key: str, token_type: str = None, select_related: Optional[List] = None,
                  prefetch_related: Optional[List] = None):
        """Возвращает токен по ключу, если его время не истекло"""
        filters = dict(
            key=key,
            moment_end__gt=tz.now(),
        )
        if token_type:
            filters['type'] = token_type
        qs = self.get_queryset()
        if select_related:
            qs = qs.select_related(*select_related)
        if prefetch_related:
            qs = qs.prefetch_related(*prefetch_related)
        try:
            return qs.get(**filters)
        except self.model.DoesNotExist:
            raise self.model.TokenIsOutdatedException()

    def delete_for_user(self, user, token_type=None):
        tokens = self.model.objects.filter(user=user)
        if token_type:
            tokens = tokens.filter(type=token_type)
        # for token in tokens:
        #     del_token_instance(token.key)
        return tokens.delete()


class BaseTokenModel(m.Model):
    key = m.CharField(__('Токен'), max_length=256, primary_key=True, blank=True)
    created_at = m.DateTimeField(__('Момент создания'), auto_now_add=True)
    moment_end = m.DateTimeField(__('Момент завершения'), blank=True)

    objects = BaseTokenManager()

    class Meta:
        abstract = True

    @staticmethod
    def generate_key(token_length):
        return generate_random_token(token_length)

    # Exceptions:
    class TokenException(Exception):
        """Логическая ошибка при обработке токенов"""

    class TokenLimitException(TokenException):
        """Превышено допустимое количество токенов для пользователя"""

    class TokenIsOutdatedException(TokenException):
        """Срок действия токена закончился"""


class SingleRowModel(m.Model):
    """ Модель для хранения единственного значения """
    value = m.TextField()

    class Meta:
        abstract = True

    @classmethod
    def get_value(cls):
        return cls.objects.first().value

    @classmethod
    def set_value(cls, value: str):
        first = cls.objects.first()
        if first is None:
            cls.objects.create(value=value)
        else:
            first.value = value
            first.save()


class ModelIterableCustomAnnotation(m.query.ModelIterable):
    def __iter__(self):
        for obj in super().__iter__():
            obj = self.queryset._annotate_exact_object(obj)
            yield obj


class QuerySetCustomAnnotations(m.QuerySet):
    """Базовый класс менеджера модели для случаев, когда необходима аннотация каждого инстанса
    чем-либо, что нельзя напрямую вытащить из БД."""

    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._iterable_class = ModelIterableCustomAnnotation
        self._custom_annotations = {}

    def annotate_with(self, **kwargs):
        clone = self._chain()
        if clone._iterable_class != ModelIterableCustomAnnotation:
            raise ValueError(f'There is no way to annotate this queryset, _iterable_class: {self._iterable_class}')
        for key, value in kwargs.items():
            clone._custom_annotations[key] = value
        return clone

    def _annotate_exact_object(self, obj):
        for key, value in self._custom_annotations.items():
            setattr(obj, key, value)
        # print(f'Annotate {obj} with: {self._custom_annotations.items()}')
        return obj

    def _clone(self):
        c = super()._clone()
        c._custom_annotations = self._custom_annotations
        return c


def one_to_one_get_or_new(instance, related_field_name, creation_kwargs=None):
    """Пытается получить объект из обратной One-to-One - связи,
     если не может, создаёт новый объект, но не сохраняет в БД."""
    rel_instance = getattr(instance, related_field_name, None)
    if rel_instance is None:
        # Вытащить модельку для related_field_name:
        relation_class = getattr(instance.__class__, related_field_name).related
        related_model = relation_class.related_model
        back_relation_field_name = relation_class.field.name
        creation_kwargs = creation_kwargs if creation_kwargs else {}
        rel_instance = related_model(**{**{back_relation_field_name: instance}, **creation_kwargs})
    return rel_instance
