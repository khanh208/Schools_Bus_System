from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, LocationLogViewSet, StopArrivalViewSet, TripIssueViewSet

router = DefaultRouter()
router.register('trips', TripViewSet, basename='trip')
router.register('locations', LocationLogViewSet, basename='location-log')
router.register('stop-arrivals', StopArrivalViewSet, basename='stop-arrival')
router.register('issues', TripIssueViewSet, basename='trip-issue')

urlpatterns = [
    path('', include(router.urls)),
]