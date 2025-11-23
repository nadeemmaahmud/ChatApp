import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatApp.settings')

django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns as chat_patterns
from calls.routing import websocket_urlpatterns as calls_patterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            chat_patterns + calls_patterns
        )
    ),
})