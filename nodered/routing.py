from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"/comms", consumers.NodeREDWebsocketProxyConsumer.as_asgi()),
    re_path(r"/dashboard/dashboard/socket\.io/", consumers.NodeREDWebsocketProxyConsumer.as_asgi()),
]
