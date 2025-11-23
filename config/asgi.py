import os
from django.core.asgi import get_asgi_application

# 1. Thiết lập môi trường
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Khởi tạo Django (BẮT BUỘC PHẢI Ở ĐÂY)
django_asgi_app = get_asgi_application()

# 3. Import các module khác (Sau khi Django setup xong)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

# Import Middleware và Consumers
from apps.authentication.middleware import JWTAuthMiddleware  # <--- ĐÃ SỬA
from apps.tracking.consumers import TripTrackingConsumer, ParentNotificationConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        # SỬ DỤNG JWTAuthMiddleware ĐỂ ĐỌC TOKEN
        JWTAuthMiddleware(
            URLRouter([
                path('ws/trips/<int:trip_id>/', TripTrackingConsumer.as_asgi()),
                path('ws/notifications/', ParentNotificationConsumer.as_asgi()),
            ])
        )
    ),
})