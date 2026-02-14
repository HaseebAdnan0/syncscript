"""
ASGI config for SyncScript project.

Supports both HTTP and WebSocket protocols.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
# before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket middleware and routing after Django is initialized
# from apps.vaults.middleware import JWTAuthMiddleware
# from apps.vaults.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        # JWTAuthMiddleware(
        #     URLRouter(websocket_urlpatterns)
        # )
        django_asgi_app  # Placeholder until middleware and routing are implemented
    ),
})
