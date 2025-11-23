from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet

router = DefaultRouter()
router.register('daily', ReportViewSet, basename='daily-report')

urlpatterns = [
    path('', include(router.urls)),
]