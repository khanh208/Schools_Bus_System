from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import uuid

from .models import User, Driver, Parent, PasswordResetToken, UserSession
from .serializers import (
    UserSerializer, DriverSerializer, ParentSerializer,
    UserRegistrationSerializer, LoginSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    TokenSerializer, ProfileSerializer, UpdateProfileSerializer,
    UserSessionSerializer, FCMTokenSerializer
)
from utils.permissions import IsAdmin, IsDriver, IsParent


class RegisterView(APIView):
    """API endpoint for user registration"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """API endpoint for user login"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Create session
            session_token = str(uuid.uuid4())
            UserSession.objects.create(
                user=user,
                session_token=session_token,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                device_info=request.data.get('device_info', '')
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Get profile data
            profile_serializer = ProfileSerializer(user)
            
            return Response({
                'user': profile_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'session_token': session_token
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """API endpoint for user logout"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Deactivate session
            session_token = request.data.get('session_token')
            if session_token:
                UserSession.objects.filter(
                    user=request.user,
                    session_token=session_token
                ).update(is_active=False)
            
            # Blacklist refresh token
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """API endpoint for changing password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """API endpoint for requesting password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = str(uuid.uuid4())
            expires_at = timezone.now() + timedelta(hours=24)
            
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Send email (implement email service)
            # EmailService.send_password_reset_email(user, token)
            
            return Response({
                'message': 'Password reset link has been sent to your email.',
                'token': token  # Remove in production, only for testing
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """API endpoint for confirming password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            token_str = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                reset_token = PasswordResetToken.objects.get(token=token_str)
                
                if not reset_token.is_valid():
                    return Response({
                        'error': 'Invalid or expired token.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update password
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                return Response({
                    'message': 'Password has been reset successfully.'
                }, status=status.HTTP_200_OK)
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Invalid token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """API endpoint for viewing and updating user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(request.user).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['username', 'email', 'full_name', 'phone']
    ordering_fields = ['created_at', 'full_name', 'last_login']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User activated successfully.'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated successfully.'})
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a user account"""
        user = self.get_object()
        user.is_verified = True
        user.save()
        return Response({'message': 'User verified successfully.'})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password (Admin only)"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response({
                'error': 'New password is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successfully.'})


class DriverViewSet(viewsets.ModelViewSet):  # <--- Đổi từ ReadOnlyModelViewSet sang ModelViewSet
    """ViewSet for viewing and editing drivers"""
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'vehicle']
    search_fields = ['user__full_name', 'license_number']
    ordering_fields = ['rating', 'experience_years']
    
    def get_permissions(self):
        # Chỉ Admin mới được quyền Thêm/Sửa/Xóa tài xế
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter available drivers
        if self.request.query_params.get('available') == 'true':
            queryset = queryset.filter(status='available')
        return queryset
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get driver performance metrics"""
        driver = self.get_object()
        
        from apps.reports.models import DriverPerformanceReport
        
        report_type = request.query_params.get('type', 'monthly')
        reports = DriverPerformanceReport.objects.filter(
            driver=driver,
            report_type=report_type
        ).order_by('-start_date')[:6]
        
        from apps.reports.serializers import DriverPerformanceReportSerializer
        
        return Response(DriverPerformanceReportSerializer(reports, many=True).data)


class ParentViewSet(viewsets.ModelViewSet):  # <--- Đổi thành ModelViewSet
    """ViewSet for viewing and editing parents"""
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['user__full_name', 'user__email', 'user__phone']
    
    def get_permissions(self):
        # Chỉ Admin mới được quyền Thêm/Sửa/Xóa phụ huynh
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get parent's children"""
        parent = self.get_object()
        children = parent.students.filter(is_active=True)
        from apps.students.serializers import StudentListSerializer
        return Response(StudentListSerializer(children, many=True).data)

class FCMTokenView(APIView):
    """API endpoint for managing FCM tokens"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Register FCM token"""
        serializer = FCMTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            from apps.notifications.models import PushToken
            
            token = serializer.validated_data['token']
            device_type = serializer.validated_data['device_type']
            device_name = serializer.validated_data.get('device_name', '')
            
            # Update or create token
            push_token, created = PushToken.objects.update_or_create(
                user=request.user,
                token=token,
                defaults={
                    'device_type': device_type,
                    'device_name': device_name,
                    'is_active': True
                }
            )
            
            return Response({
                'message': 'FCM token registered successfully.',
                'token_id': push_token.id
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Remove FCM token"""
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.notifications.models import PushToken
        
        deleted_count = PushToken.objects.filter(
            user=request.user,
            token=token
        ).delete()[0]
        
        return Response({
            'message': f'{deleted_count} token(s) removed successfully.'
        })


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing user sessions"""
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a specific session"""
        session = self.get_object()
        session.is_active = False
        session.save()
        
        return Response({'message': 'Session terminated successfully.'})
    
    @action(detail=False, methods=['post'])
    def terminate_all(self, request):
        """Terminate all sessions except current"""
        current_token = request.data.get('current_session_token')
        
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(session_token=current_token).update(is_active=False)
        
        return Response({'message': 'All other sessions terminated successfully.'})