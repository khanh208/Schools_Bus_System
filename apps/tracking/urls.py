from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, LocationLogViewSet, StopArrivalViewSet, TripIssueViewSet
from .parent_views import ParentTrackingViewSet, parent_tracking_page, parent_tracking_demo

router = DefaultRouter()
router.register('trips', TripViewSet, basename='trip')
router.register('locations', LocationLogViewSet, basename='location-log')
router.register('stop-arrivals', StopArrivalViewSet, basename='stop-arrival')
router.register('issues', TripIssueViewSet, basename='trip-issue')
router.register('parent/tracking', ParentTrackingViewSet, basename='parent-tracking')

urlpatterns = [
    path('', include(router.urls)),
    path('parent/map/', parent_tracking_page),
    path('parent/demo/', parent_tracking_demo),
]