# apps/tracking/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TripViewSet, LocationLogViewSet, StopArrivalViewSet
from .parent_views import (
    ParentTrackingViewSet,
    parent_tracking_page,
    parent_tracking_demo,
)

router = DefaultRouter()

# API chính cho tracking
router.register('trips', TripViewSet, basename='trip')
router.register('locations', LocationLogViewSet, basename='location-log')
router.register('stops', StopArrivalViewSet, basename='stop-arrival')

# API cho phụ huynh (ReadOnly)
router.register('parent/trips', ParentTrackingViewSet, basename='parent-trip')

urlpatterns = [
    path('', include(router.urls)),

    # Trang/demo cho phụ huynh
    path('parent/', parent_tracking_page, name='parent-tracking-page'),
    path('parent/demo/', parent_tracking_demo, name='parent-tracking-demo'),
]
