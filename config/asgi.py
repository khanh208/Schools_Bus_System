# config/asgi.py - Complete WebSocket Configuration
import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path  # 👈 nhớ import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

# Chỉ import những consumer thực sự tồn tại
from apps.tracking.consumers import TripTrackingConsumer, ParentNotificationConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path('ws/trips/<int:trip_id>/', TripTrackingConsumer.as_asgi()),
                path('ws/notifications/', ParentNotificationConsumer.as_asgi()),
            ])
        )
    ),
})
