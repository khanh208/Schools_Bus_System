from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, NotificationPreferenceViewSet,
    NotificationTemplateViewSet, BulkNotificationViewSet
)

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notification')
router.register('preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register('templates', NotificationTemplateViewSet, basename='notification-template')
router.register('bulk', BulkNotificationViewSet, basename='bulk-notification')

urlpatterns = [
    path('', include(router.urls)),
]