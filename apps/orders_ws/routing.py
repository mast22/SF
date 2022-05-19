from django.urls import path
from . import consumers

# Все пути необходимо назначать начиная с "ws" для правильного проксирования на nginx
websocket_urlpatterns = [
    path('ws/order-updates/', consumers.AgentConsumer.as_asgi()),
]
