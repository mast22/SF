from rest_framework_nested.routers import DefaultRouter as drf_DefaultRouter, NestedMixin


class DefaultRouter(drf_DefaultRouter):
    """Обёртка над DefaultRouter, которая добавляет register_resource"""

    def register_resource(self, viewset, basename=None, prefix=None):
        meta = getattr(viewset, 'JSONAPIMeta', None)
        if meta is None:
            model = viewset.queryset.model
            meta = getattr(model, 'JSONAPIMeta', object)
        if meta is not None:
            if prefix is None:
                prefix = getattr(meta, 'resource_name', None)
        assert prefix is not None, f'Wrong viewset: {viewset}, there is no resource_name in it,' \
                                   f' use router.register for such views!'
        return self.register(prefix=prefix, viewset=viewset, basename=basename)

    def _get_prefix(self):
        return None


class NestedRouter(NestedMixin, DefaultRouter):
    pass
