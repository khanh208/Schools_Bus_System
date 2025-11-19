# config/asgi.py - Complete WebSocket Configuration
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from apps.tracking.consumers import TripTrackingConsumer, NotificationConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path('ws/trips/<int:trip_id>/', TripTrackingConsumer.as_asgi()),
                path('ws/notifications/', NotificationConsumer.as_asgi()),
            ])
        )
    ),
})