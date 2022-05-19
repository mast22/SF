"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.utils import model_meta



def create_instance_inner(serializer, instance=None):
    v_data = serializer.validated_data

    if instance is not None:
        model_class = instance.__class__
    elif hasattr(serializer, 'Meta'):
        # Model serializer
        model_class = serializer.Meta.model
    else:
        # Non-model serializer, can't check the model class creation, just skip:
        return None

    info = model_meta.get_field_info(model_class)
    many_to_many = {}
    for field_name, relation_info in info.relations.items():
        if relation_info.to_many and (field_name in v_data):
            many_to_many[field_name] = v_data[field_name]

    v_data = {k:v for k,v in v_data.items() if k not in many_to_many}

    if instance is None:
        instance = model_class(**v_data)

    instance._validated_data = v_data
    instance._validated_data_many_to_many = many_to_many
    return instance


class CreateModelMixin:
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        assert isinstance(self, GenericViewSet) and isinstance(self, CreateModelMixin)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance_newdata = create_instance_inner(serializer)
        self.check_object_permissions(request, instance_newdata)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    def perform_create(self, serializer, **kwargs):
        serializer.save(**kwargs)



class UpdateModelMixin:
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        assert isinstance(self, GenericViewSet) and isinstance(self, UpdateModelMixin)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # May raise a permission denied
        instance_newdata = create_instance_inner(serializer, instance)
        self.check_object_permissions(self.request, instance_newdata)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer, **kwargs):
        serializer.save(**kwargs)


# class ListModelMixin:
#     """List a queryset."""
#     def list(self, request, *args, **kwargs):
#         assert isinstance(self, GenericViewSet)
#         queryset = self.filter_queryset(self.get_queryset())
#         page = self.paginate_queryset(queryset)
#
#         if page is not None and self.paginator is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)
#
#
# class RetrieveModelMixin:
#     """
#     Retrieve a model instance.
#     """
#     def retrieve(self, request, *args, **kwargs):
#         assert isinstance(self, GenericViewSet)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)
#
#     def get_object(self):
#         """
#         Returns the object the view is displaying.
#
#         You may want to override this if you need to provide non-standard
#         queryset lookups.  Eg if objects are referenced using multiple
#         keyword arguments in the url conf.
#         """
#         assert isinstance(self, GenericViewSet)
#         if getattr(self, 'use_optional_fields', False):
#             qs = self.filter_queryset(self.get_queryset())
#             queryset = self.get_queryset().filter(pk__in=qs.values('pk'))
#         else:
#             queryset = self.filter_queryset(self.get_queryset())
#
#         # Perform the lookup filtering.
#         lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
#
#         assert lookup_url_kwarg in self.kwargs, (
#             'Expected view %s to be called with a URL keyword argument '
#             'named "%s". Fix your URL conf, or set the `.lookup_field` '
#             'attribute on the view correctly.' %
#             (self.__class__.__name__, lookup_url_kwarg)
#         )
#
#         filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
#         obj = get_object_or_404(queryset, **filter_kwargs)
#
#         # May raise a permission denied
#         self.check_object_permissions(self.request, obj)
#
#         return obj



class DestroyModelMixin:
    def destroy(self, request, *args, **kwargs):
        assert isinstance(self, GenericViewSet) and isinstance(self, DestroyModelMixin)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except IntegrityError as e:
            raise ValidationError('Удаление данной записи невозможно.'
                                  ' Это приведёт к нарушению согласованности данных. '
                                  f'Сперва очистите все зависящие от неё записи. Ошибка: {e}')
