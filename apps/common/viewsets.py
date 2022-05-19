from django.utils.decorators import classonlymethod
from rest_framework.viewsets import GenericViewSet
from rest_framework.settings import api_settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework_json_api import views

from rest_framework.metadata import SimpleMetadata
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from rest_framework_json_api.metadata import JSONAPIMetadata
from rest_framework_json_api.renderers import JSONRenderer as JSONAPI_JSONRenderer
from rest_framework_json_api.parsers import JSONParser as JSONAPI_JSONParser
from apps.common.pagination import JsonApiPageNumberPagination, PageNumberPagination
from apps.common import viewsets_mixins as mixins


DEFAULT_ACTIONS = {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}


class CustomParametersMixin:
    format_based_parameters = {
        'json': {
            'pagination_class': PageNumberPagination,
            'metadata_class': SimpleMetadata,
            'renderer_classes': (JSONRenderer,),
            'parser_classes': (JSONParser,)
            # 'exception_handler': exception_handler,
        },
        'vnd.api+json': {
            'pagination_class': JsonApiPageNumberPagination,
            'metadata_class': JSONAPIMetadata,
            'renderer_classes': (JSONAPI_JSONRenderer,),
            'parser_classes': (JSONAPI_JSONParser,)
            # 'exception_handler': JSONAPI_exception_handler,
        },
    }

    # Можно добавить различные сериалайзеры в зависимости от action и format или header-а Accepted
    # Пример:
    # custom_serializer_classes = {
    #    'create': CustomCreateSerializer,
    #    'list': { 'json': CustomListSerializer },
    # }
    custom_serializer_classes = {}

    # Сортировка по умолчанию: можно сортировать по любому полю, если не задано явно - сортировать по id
    ordering_fields = '__all__'
    ordering = 'id'

    # Список action, для которых используем JSON-API, по умолчанию - все REST-actions
    json_api_actions = DEFAULT_ACTIONS

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        super().__init__(**kwargs)
        self._current_format = None
        self._current_parameters = None

    @classmethod
    def _init_format_based_params(cls, actions, initkwargs: dict):
        """Изменяет аргументы класса в зав-ти от action"""
        is_json_api = False
        for action in actions.values():
            if action in cls.json_api_actions:
                is_json_api = True
                break

        if is_json_api:
            format_key = 'vnd.api+json'
        else:
            format_key = 'json'
        if 'renderer_classes' not in initkwargs:
            initkwargs['renderer_classes'] = tuple(cls.format_based_parameters[format_key]['renderer_classes'])\
                + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

        if 'parser_classes' not in initkwargs:
            initkwargs['parser_classes'] = tuple(cls.format_based_parameters[format_key]['parser_classes'])\
                + tuple(api_settings.DEFAULT_PARSER_CLASSES)

        format_based = cls.format_based_parameters[format_key]
        initkwargs_combined = {**format_based, **initkwargs}

        return initkwargs_combined

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        # # Custom action
        # ex1 = {'get': 'client_refused'}
        # # api/elements/
        # ex2 = {'get': 'list', 'post': 'create'}
        # # api/elements/1/
        # ex3 = {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
        assert issubclass(cls, GenericViewSet) and issubclass(cls, CustomParametersMixin)
        initkwargs = cls._init_format_based_params(actions, initkwargs)
        return super().as_view(actions=actions, **initkwargs)

    def get_exception_handler(self):
        """
        Returns the exception handler that this view uses.
        """
        return self.settings.EXCEPTION_HANDLER

    def _get_current_format_from_url(self):
        format = self.request.query_params.get('format', None)
        if format == 'openapi':
            format = None
        return format

    # def _get_current_format_from_header(self):
    #     accepted_header = self.request.headers.get('Accept')
    #     if accepted_header:
    #         accepted_header_parts = accepted_header.split(',')
    #         # 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    #         for renderer_class in self.renderer_classes:
    #             if renderer_class.media_type in accepted_header_parts:
    #                 return renderer_class.format
    #     return None

    def _get_current_format_by_action(self):
        action = self.action
        return 'vnd.api+json' if action in self.json_api_actions else 'json'

    def get_current_format(self):
        """Get response format depended of format parameter or Accept header"""
        if self._current_format is None:
            # # Сперва ищем явно заданный format в URL
            self._current_format = self._get_current_format_from_url()
            if self._current_format is not None:
                return self._current_format

            # # Далее смотрим на header ACCEPT
            # self._current_format = self._get_current_format_from_header()
            # if self._current_format is not None:
            #     return self._current_format

            # Далее возвращаем format в зависимости от action.
            self._current_format = self._get_current_format_by_action()
            # print(f'ACTION: {self.action} FORMAT: {self._current_format} view: {self.__class__} {self.get_view_name()}')
        return self._current_format

    def get_current_parameters(self):
        if self._current_parameters is None:
            cur_format = self.get_current_format()
            self._current_parameters = self.format_based_parameters.get(cur_format, {})
        return self._current_parameters

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            pagination_class = self.get_pagination_class()
            self._paginator = pagination_class()
            # print('PAGINATION:', type(self._paginator), self._paginator)
        return self._paginator

    def get_pagination_class(self):
        cur_parameters = self.get_current_parameters()
        return cur_parameters.get('pagination_class', self.pagination_class)


    def get_serializer_class(self):
        """Возвращает Serializer в зависимости от action и format"""
        serializer_class = self.serializer_class

        if self.custom_serializer_classes and self.action:
            serializer_class = self.custom_serializer_classes.get(self.action, self.serializer_class)
            if isinstance(serializer_class, dict):
                resp_format = self.get_current_format()
                serializer_class = serializer_class.get(resp_format, self.serializer_class)
        return serializer_class

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def options(self, request, *args, **kwargs):
        """
        Handler method for HTTP 'OPTIONS' request.
        """
        cur_parameters = self.get_current_parameters()
        metadata_class = cur_parameters.get('metadata_class', self.metadata_class)
        if metadata_class is None:
            return self.http_method_not_allowed(request, *args, **kwargs)
        data = metadata_class().determine_metadata(request, self)
        return Response(data, status=status.HTTP_200_OK)


class CustomQuerySetMixin:
    # Можно добавить различные QuerySet в зависимости от action
    custom_querysets = {}

    def get_custom_queryset(self):
        return self.custom_querysets.get(self.action, self.queryset)

    def get_queryset(self, *args, **kwargs):
        """Возвращает QuerySet в зависимости от action"""
        queryset = self.get_custom_queryset()
        if self.request is None:
            return queryset.none()
        # Ensure queryset is re-evaluated on each request.
        return queryset.all()


class WithStatsMixin:
    """Проверяет наличие параметра with-stats=some в url, при """
    with_stats_param = 'with-stats'
    querysets_with_stats = {}

    def _get_with_stats(self):
        with_stats = self.request.query_params.get(self.with_stats_param, None)
        with_stats = str(with_stats) if with_stats else None
        # with_stats = u.string_to_boolean(with_stats)
        return with_stats

    def get_queryset(self, with_stats=True, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        with_stats = self._get_with_stats()
        if with_stats:
            qs = self.with_stats(qs, with_stats, args, kwargs)
        return qs

    def with_stats(self, qs, with_stats, args=None, kwargs=None):
        method = self.querysets_with_stats.get(with_stats, None)
        if isinstance(method, str):
            method = getattr(self, method, None)

        if method is None:
            raise NotImplementedError('No stats could be loaded!')

        return method(qs, with_stats, *args, **kwargs)



class PermissionsFilteringMixin(GenericViewSet):
    """Добавляет фильтр по permission, при наличии таковых"""
    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        Add filter by permission_classes if they have "filter_queryset" method.
        """
        queryset = super().filter_queryset(queryset)

        for permission_backend in list(self.permission_classes):
            if hasattr(permission_backend, 'filter_queryset'):
                queryset = permission_backend().filter_queryset(self.request, queryset, self)
        return queryset



# class AdaptiveFiltersMixin:
#     # При получении get-параметра format=adaptive-filters вернуть фильтры вместо результата
#     adaptive_filters_lookup = 'adaptive-filters'
#
#     # Поля, по которым можно отфильтровать queryset в формате:
#     # { 'filter_name': {'type': 'Тип параметра', 'lookup': 'field__lookup_to_filter'}
#     adaptive_filters = {}
#
#     def __init__(self, **kwargs):
#         """
#         Constructor. Called in the URLconf; can contain helpful extra
#         keyword arguments, and other things.
#         """
#         # Go through keyword arguments, and either save their values to our
#         # instance, or raise an error.
#         super().__init__(**kwargs)
#         self._current_format = None
#
#     def _check_for_adaptive_filters_format(self):
#         is_adaptive_filters = self.request.query_params.get(self.adaptive_filters_lookup, False)
#         if type(is_adaptive_filters) is str:
#             is_adaptive_filters = u.string_to_boolean(is_adaptive_filters)
#         return bool(is_adaptive_filters)
#
#     def list(self, *args, **kwargs):
#         if self._check_for_adaptive_filters_format():
#             return self.process_filters(*args, **kwargs)
#         else:
#             return super().list(*args, **kwargs)
#
#     def process_filters(self, *args, **kwargs):
#         data = {'detail': 'not implemented yet!'}
#
#         # Django-filters-like filters.
#         qs = self.filter_queryset(self.get_queryset())
#         for key, props in self.adaptive_filters.items():
#             pass
#
#         return Response(data, status=status.HTTP_200_OK)


class CreatedByMixin:
    """Сохраняет текущего пользователя в поле created_by"""

    # Поле модели, в которое необходимо сохранить текущего пользователя
    field_created_by = 'created_by'

    def perform_create(self, serializer, **kwargs):
        kwargs[self.field_created_by] = self.request.user
        serializer.save(**kwargs)


class ListModelMixin(mixins.ListModelMixin):
    aggregated_stats_param = 'aggregated_stats'

    def _get_aggregated_stats_requested(self, request):
        return self.aggregated_stats_param in self.request.query_params

    def list(self, request, *args, **kwargs):
        """ Переписанный list для внедрения в pagination значений в мету """
        aggregated_stats = getattr(self, 'aggregated_stats', False)
        stats_requested = self._get_aggregated_stats_requested(request)
        if aggregated_stats and stats_requested:
            queryset = self.filter_queryset(self.get_queryset())
            evaludated_stats = aggregated_stats(queryset)

            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            # FIXME придумать идею получще, меняю передаваемые аргументы функции
            #  из-за этого напрямую обращаюсь к пагинатору, это может вызвать проблемы
            return self.paginator.get_paginated_response(serializer.data, evaludated_stats)
        return super(ListModelMixin, self).list(request, *args, **kwargs)


class ReadOnlyModelViewSet(
    CustomParametersMixin,
    # AdaptiveFiltersMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    views.AutoPrefetchMixin,
    views.PreloadIncludesMixin,
    views.RelatedMixin,
    CustomQuerySetMixin,
    GenericViewSet,
):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass


class ListOnlyModelViewSet(
    CustomParametersMixin,
    mixins.ListModelMixin,
    views.AutoPrefetchMixin,
    views.PreloadIncludesMixin,
    views.RelatedMixin,
    CustomQuerySetMixin,
    PermissionsFilteringMixin,
    GenericViewSet,
):
    """A viewset that provides only default `list` action."""


class ModelViewSet(
    CustomParametersMixin,
    mixins.RetrieveModelMixin,
    ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    views.AutoPrefetchMixin,
    views.PreloadIncludesMixin,
    views.RelatedMixin,
    CustomQuerySetMixin,
    PermissionsFilteringMixin,
    GenericViewSet,
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass


class NoDestroyModelViewSet(
    CustomParametersMixin,
    mixins.RetrieveModelMixin,
    ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    views.AutoPrefetchMixin,
    views.PreloadIncludesMixin,
    views.RelatedMixin,
    CustomQuerySetMixin,
    PermissionsFilteringMixin,
    GenericViewSet,
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass


class CreateListRetrieveModelViewSet(
    CustomParametersMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    views.AutoPrefetchMixin,
    views.PreloadIncludesMixin,
    views.RelatedMixin,
    CustomQuerySetMixin,
    PermissionsFilteringMixin,
    GenericViewSet,
):
    """ Вьюсет для создания и перечисления клиентов """
    pass