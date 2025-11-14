from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassViewSet, AreaViewSet, StudentViewSet,
    StudentNoteViewSet, StudentDocumentViewSet,
    EmergencyContactViewSet
)

router = DefaultRouter()
router.register('classes', ClassViewSet, basename='class')
router.register('areas', AreaViewSet, basename='area')
router.register('students', StudentViewSet, basename='student')
router.register('notes', StudentNoteViewSet, basename='student-note')
router.register('documents', StudentDocumentViewSet, basename='student-document')
router.register('emergency-contacts', EmergencyContactViewSet, basename='emergency-contact')

urlpatterns = [
    path('', include(router.urls)),
]