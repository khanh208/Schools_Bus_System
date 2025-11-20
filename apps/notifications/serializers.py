# apps/notifications/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer chi tiết cho 1 notification"""

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = ['id', 'read_at', 'created_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer nhẹ dùng cho list / unread"""

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'is_read',
            'created_at',
        ]


class MarkAsReadSerializer(serializers.Serializer):
    """Payload để đánh dấu đã đọc"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    mark_all = serializers.BooleanField(default=False)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer cho notification preferences (bản đơn giản)"""

    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'enable_notifications',
            'attendance_notifications',
            'trip_notifications',
            'eta_notifications',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
