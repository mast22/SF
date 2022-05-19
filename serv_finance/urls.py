import debug_toolbar
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from apps.api.urls import urlpatterns, app_name

urlpatterns = [
    path('api/', include((urlpatterns, app_name), namespace='api')),
]

if settings.DEBUG:
    from schema_graph.views import Schema
    urlpatterns = [
        path('api-auth/', include('rest_framework.urls')),
    ] + urlpatterns + [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
        path('schema/', Schema.as_view()),
    ]


# Monkey patch drf_yasg_json_api
from drf_yasg_json_api.inspectors.view import SwaggerAutoSchema

def new_get_query_parameters(self):
    return super(SwaggerAutoSchema, self).get_query_parameters()

SwaggerAutoSchema.get_query_parameters = new_get_query_parameters
