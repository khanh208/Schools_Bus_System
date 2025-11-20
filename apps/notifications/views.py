# apps/notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationPreferenceSerializer,
    MarkAsReadSerializer,
)
from utils.pagination import StandardResultsSetPagination


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho notification in-app (bản đơn giản)
    - GET /api/notifications/            -> list thông báo của user
    - GET /api/notifications/unread/     -> list thông báo chưa đọc
    - POST /api/notifications/mark_as_read/  -> đánh dấu đã đọc
    - POST /api/notifications/{id}/mark_read/ -> đánh dấu 1 cái
    - DELETE /api/notifications/clear_all/ -> xóa hết thông báo
    """
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'is_read']

    def get_queryset(self):
        # Chỉ trả về notification của user hiện tại
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_serializer_class(self):
        # List / unread dùng serializer nhẹ
        if self.action in ['list', 'unread']:
            return NotificationListSerializer
        return NotificationSerializer

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Lấy danh sách thông báo chưa đọc"""
        qs = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """
        Đánh dấu đã đọc:
        - mark_all = true -> đánh dấu tất cả
        - notification_ids = [1,2,3] -> đánh dấu danh sách id
        """
        serializer = MarkAsReadSerializer(data=request.data)
        if serializer.is_valid():
            mark_all = serializer.validated_data.get('mark_all', False)
            ids = serializer.validated_data.get('notification_ids', [])

            qs = self.get_queryset()
            if mark_all:
                count = qs.filter(is_read=False).update(
                    is_read=True,
                    read_at=timezone.now(),
                )
                return Response(
                    {'message': f'Marked {count} notifications as read.'}
                )
            else:
                if not ids:
                    return Response(
                        {'error': 'notification_ids is required when mark_all is false.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                updated = qs.filter(id__in=ids).update(
                    is_read=True,
                    read_at=timezone.now(),
                )
                return Response(
                    {'message': f'Marked {updated} notifications as read.'}
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Đánh dấu 1 notification là đã đọc"""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response({'message': 'Notification marked as read.'})

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Xóa tất cả thông báo của user hiện tại"""
        qs = self.get_queryset()
        count = qs.delete()[0]
        return Response({'message': f'Deleted {count} notifications.'})
    

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho notification preferences (bản đơn giản)
    - GET /api/notifications/preferences/my_preferences/
    - POST /api/notifications/preferences/update_preferences/
    """
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Lấy config notification của user hiện tại"""
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(prefs)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update config notification của user hiện tại"""
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(prefs, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
