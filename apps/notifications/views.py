# apps/notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    BulkNotification
)
from .serializers import (
    NotificationSerializer, NotificationPreferenceSerializer,
    NotificationTemplateSerializer, BulkNotificationSerializer,
    MarkAsReadSerializer, SendNotificationSerializer
)
from utils.permissions import IsAdmin
from utils.pagination import StandardResultsSetPagination


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for user notifications"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'is_read', 'sent_via']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Mark notifications as read"""
        serializer = MarkAsReadSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('mark_all'):
                Notification.mark_all_as_read(request.user)
                return Response({'message': 'All notifications marked as read'})
            else:
                notification_ids = serializer.validated_data.get('notification_ids', [])
                Notification.objects.filter(
                    user=request.user,
                    id__in=notification_ids
                ).update(is_read=True, read_at=timezone.now())
                return Response({'message': f'{len(notification_ids)} notifications marked as read'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Clear all notifications"""
        count = self.get_queryset().delete()[0]
        return Response({'message': f'Deleted {count} notifications'})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for notification preferences"""
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(prefs)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(prefs, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for notification templates (Admin only)"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'is_active']


class BulkNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for bulk notifications (Admin only)"""
    queryset = BulkNotification.objects.all()
    serializer_class = BulkNotificationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardResultsSetPagination
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send bulk notification"""
        serializer = SendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            # Import notification service
            from .services import NotificationService
            
            recipient_type = serializer.validated_data['recipient_type']
            user_ids = serializer.validated_data.get('user_ids', [])
            
            # Get recipients
            from apps.authentication.models import User
            if recipient_type == 'all_users':
                users = User.objects.filter(is_active=True)
            elif recipient_type == 'all_parents':
                users = User.objects.filter(role='parent', is_active=True)
            elif recipient_type == 'all_drivers':
                users = User.objects.filter(role='driver', is_active=True)
            elif recipient_type == 'specific_users':
                users = User.objects.filter(id__in=user_ids, is_active=True)
            
            # Send notifications
            sent_count = 0
            for user in users:
                Notification.objects.create(
                    user=user,
                    title=serializer.validated_data['title'],
                    message=serializer.validated_data['message'],
                    notification_type=serializer.validated_data['notification_type'],
                    sent_via='in_app'
                )
                sent_count += 1
            
            return Response({
                'message': f'Sent {sent_count} notifications',
                'sent_count': sent_count
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)