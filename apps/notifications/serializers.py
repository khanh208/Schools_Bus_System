from rest_framework import serializers
from .models import (
    NotificationTemplate, Notification, NotificationPreference,
    NotificationLog, BulkNotification, PushToken
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'code', 'title', 'message_template',
            'notification_type', 'send_push', 'send_email',
            'send_sms', 'send_in_app', 'is_active', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'notification_type',
            'sent_via', 'is_read', 'read_at', 'priority',
            'action_url', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'is_read', 'priority', 'created_at'
        ]


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'enable_push', 'enable_email', 'enable_sms',
            'enable_in_app', 'attendance_notifications',
            'trip_start_notifications', 'trip_end_notifications',
            'delay_notifications', 'eta_notifications',
            'emergency_notifications', 'quiet_hours_enabled',
            'quiet_hours_start', 'quiet_hours_end', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification', 'user', 'username', 'channel',
            'status', 'recipient', 'message_id', 'error_message',
            'sent_at', 'delivered_at', 'failed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BulkNotificationSerializer(serializers.ModelSerializer):
    """Serializer for bulk notifications"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = BulkNotification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'recipient_type', 'recipient_ids', 'send_push',
            'send_email', 'send_sms', 'send_in_app',
            'scheduled_at', 'status', 'total_recipients',
            'sent_count', 'failed_count', 'created_by',
            'created_by_name', 'created_at', 'sent_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_recipients', 'sent_count',
            'failed_count', 'created_by', 'created_at', 'sent_at'
        ]


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending custom notifications"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    recipient_type = serializers.ChoiceField(
        choices=['all_users', 'all_parents', 'all_drivers', 'specific_users'],
        required=True
    )
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(
        choices=['info', 'warning', 'alert', 'success']
    )
    send_push = serializers.BooleanField(default=True)
    send_email = serializers.BooleanField(default=False)
    send_sms = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        if attrs['recipient_type'] == 'specific_users' and not attrs.get('user_ids'):
            raise serializers.ValidationError({
                "user_ids": "User IDs are required when recipient_type is 'specific_users'."
            })
        return attrs


class PushTokenSerializer(serializers.ModelSerializer):
    """Serializer for push tokens"""
    
    class Meta:
        model = PushToken
        fields = [
            'id', 'user', 'token', 'device_type', 'device_name',
            'is_active', 'created_at', 'last_used'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'last_used']