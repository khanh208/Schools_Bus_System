# apps/attendance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceViewSet, AttendanceExceptionViewSet,
    AttendanceReportViewSet, AttendanceAlertViewSet
)

router = DefaultRouter()
router.register('records', AttendanceViewSet, basename='attendance')
router.register('exceptions', AttendanceExceptionViewSet, basename='attendance-exception')
router.register('reports', AttendanceReportViewSet, basename='attendance-report')
router.register('alerts', AttendanceAlertViewSet, basename='attendance-alert')

urlpatterns = [
    path('', include(router.urls)),
]