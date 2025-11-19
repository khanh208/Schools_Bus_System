from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from apps.tracking.consumers import TripTrackingConsumer, NotificationConsumer, ParentNotificationConsumer

websocket_urlpatterns = [
    path('ws/trip/<int:trip_id>/', TripTrackingConsumer.as_asgi()),
    path('ws/notifications/', ParentNotificationConsumer.as_asgi()),
]
application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})