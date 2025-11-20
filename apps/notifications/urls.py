# apps/notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationViewSet,
    NotificationPreferenceViewSet,
)

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notification')
router.register('preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('', include(router.urls)),
]
