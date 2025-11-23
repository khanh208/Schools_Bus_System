# config/routing.py
from django.urls import path
from apps.tracking.consumers import TripTrackingConsumer, ParentNotificationConsumer

# Tất cả WebSocket endpoint của project
websocket_urlpatterns = [
    path("ws/trips/<int:trip_id>/", TripTrackingConsumer.as_asgi()),
    path("ws/notifications/", ParentNotificationConsumer.as_asgi()),
]