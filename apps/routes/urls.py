from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet, RouteViewSet, RouteStopViewSet,
    StudentRouteViewSet, RouteScheduleViewSet
)

router = DefaultRouter()
router.register('vehicles', VehicleViewSet, basename='vehicle')
router.register('routes', RouteViewSet, basename='route')
router.register('stops', RouteStopViewSet, basename='route-stop')
router.register('assignments', StudentRouteViewSet, basename='student-route')
router.register('schedules', RouteScheduleViewSet, basename='route-schedule')

urlpatterns = [
    path('', include(router.urls)),
]