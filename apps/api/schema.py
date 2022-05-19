from django.urls import path
# from django.views.decorators.cache import cache_page
# from django.conf import settings
from rest_framework import permissions as p
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


api_info = openapi.Info(
    title='Service Finance API',
    default_version='v1',
    description='Swagger схема api для работы с системой Сервис-Финанс',
    contact=openapi.Contact(email="[email protected]"),
)


schema_view = get_schema_view(api_info, public=True, permission_classes=(p.AllowAny,))


urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
