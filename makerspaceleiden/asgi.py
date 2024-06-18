import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from selfservice.aggregator_adapter import initialize_aggregator_adapter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "makerspaceleiden.settings")

_application = get_asgi_application()

from nodered.routing import websocket_urlpatterns  # noqa: E402


def initialized_application():
    initialize_aggregator_adapter(
        os.environ.get("AGGREGATOR_BASE_URL", "http://127.0.0.1:5000"),
        os.environ.get("AGGREGATOR_USERNAME", "user"),
        os.environ.get("AGGREGATOR_PASSWORD", "pass"),
    )
    return _application


application = ProtocolTypeRouter(
    {
        "http": initialized_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
