from channels.routing import ProtocolTypeRouter, URLRouter
from apps.orders_ws.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': URLRouter(
        websocket_urlpatterns
    ),
})
