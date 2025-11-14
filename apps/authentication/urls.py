from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, ChangePasswordView,
    PasswordResetRequestView, PasswordResetConfirmView,
    ProfileView, UserViewSet, DriverViewSet, ParentViewSet,
    FCMTokenView, SessionViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('drivers', DriverViewSet, basename='driver')
router.register('parents', ParentViewSet, basename='parent')
router.register('sessions', SessionViewSet, basename='session')

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password Management
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # FCM Tokens
    path('fcm-token/', FCMTokenView.as_view(), name='fcm_token'),
    
    # Router URLs
    path('', include(router.urls)),
]