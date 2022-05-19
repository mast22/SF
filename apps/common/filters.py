from django.db.models import QuerySet
from django_filters import FilterSet as df_FilterSet

# from rest_framework_json_api.django_filters import DjangoFilterBackend
# from rest_framework_json_api.utils import format_value
# from rest_framework.exceptions import ValidationError
# from rest_framework.settings import api_settings
# import re



class FilterSet(df_FilterSet):
    """Eсли указать параметр Meta.grouped_filters, то перечисленные в нём фильтры должны возвращать
    словарь параметров, которые будут применены к queryset совместно.
    Пример:
    def filter_by_my_param(queryset, name, value):
        return {f'{name}__icontains': value}
    class MyCoolFilter(FilterSet):
        my_param = NumericFilter(method=filter_my_param)
        class Meta:
            grouped_filters = {'my_param'}
    """
    def filter_queryset(self, queryset: QuerySet):
        filter_kwargs = {}
        grouped_filters = getattr(getattr(self, 'Meta', object), 'grouped_filters', tuple())
        for name, value in self.form.cleaned_data.items():
            if name in grouped_filters:
                filter_new_kwargs = self.filters[name].filter(queryset, value)
                if isinstance(filter_new_kwargs, dict):
                    filter_kwargs.update(filter_new_kwargs)
            else:
                queryset = self.filters[name].filter(queryset, value)
                assert isinstance(queryset, QuerySet), \
                    "Expected '%s.%s' to return a QuerySet, but got a %s instead." \
                    % (type(self).__name__, name, type(queryset).__name__)
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset



# class AdaptiveDjangoFilterBackend(DjangoFilterBackend):
#     # Parent:
#     # def get_filterset_kwargs(self, request, queryset, view):
#     #     return {
#     #         'data': request.query_params,
#     #         'queryset': queryset,
#     #         'request': request,
#     #     }
#
#     # Example of adaptive filters:
#     # adaptive_filters = {
#     #     'ter_manager': {'type': 'foreign_key', 'lookup': 'region__ter_manager'},
#     #     'region': {'type': 'foreign_key', 'lookup': 'region'},
#     #     'outlet': {'type': 'foreign_key', 'lookup': 'outlet_agents__outlet'},
#     # }
#
#     def get_filterset_kwargs(self, request, queryset, view):
#         """
#         Turns filter[<field>]=<value> into <field>=<value> which is what
#         DjangoFilterBackend expects
#
#         :raises ValidationError: for bad filter syntax
#         """
#         filter_keys = []
#         # rewrite filter[field] query params to make DjangoFilterBackend work.
#         data = request.query_params.copy()
#         for qp, val in request.query_params.lists():
#             m = self.filter_regex.match(qp)
#             if m and (not m.groupdict()['assoc'] or
#                       m.groupdict()['ldelim'] != '[' or m.groupdict()['rdelim'] != ']'):
#                 raise ValidationError("invalid query parameter: {}".format(qp))
#             if m and qp != self.search_param:
#                 if not all(val):
#                     raise ValidationError("missing value for query parameter {}".format(qp))
#                 # convert jsonapi relationship path to Django ORM's __ notation
#                 key = m.groupdict()['assoc'].replace('.', '__')
#                 # undo JSON_API_FORMAT_FIELD_NAMES conversion:
#                 key = format_value(key, 'underscore')
#                 data.setlist(key, val)
#                 filter_keys.append(key)
#                 del data[qp]
#         return {
#             'data': data,
#             'queryset': queryset,
#             'request': request,
#             'filter_keys': filter_keys,
#         }

