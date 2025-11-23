from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BackupViewSet

router = DefaultRouter()
router.register('logs', BackupViewSet, basename='backup-log')

urlpatterns = [
    path('', include(router.urls)),
]