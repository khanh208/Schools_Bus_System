from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class NotificationType(models.TextChoices):
    INFO = 'info', 'Information'
    WARNING = 'warning', 'Warning'
    ALERT = 'alert', 'Alert'
    SUCCESS = 'success', 'Success'
    ERROR = 'error', 'Error'


class NotificationChannel(models.TextChoices):
    PUSH = 'push', 'Push Notification'
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    IN_APP = 'in_app', 'In-App'


class NotificationTemplate(models.Model):
    """Reusable notification templates"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    message_template = models.TextField(
        help_text="Use {variable_name} for dynamic content"
    )
    notification_type = models.CharField(
        max_length=50, 
        choices=NotificationType.choices
    )
    
    # Channels
    send_push = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    send_in_app = models.BooleanField(default=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=1,
        help_text="1=Low, 2=Medium, 3=High, 4=Critical"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def render(self, context):
        """Render template with context data"""
        title = self.title.format(**context)
        message = self.message_template.format(**context)
        return title, message


class Notification(models.Model):
    """Individual notification records"""
    user = models.ForeignKey(
        'authentication.User', 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50, 
        choices=NotificationType.choices
    )
    
    # Related object (generic relation)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Delivery
    sent_via = models.CharField(
        max_length=50, 
        choices=NotificationChannel.choices
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Priority
    priority = models.IntegerField(default=1)
    
    # Action URL (for deep linking)
    action_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a user"""
        cls.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(
        'authentication.User', 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    # Channel preferences
    enable_push = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_in_app = models.BooleanField(default=True)
    
    # Notification types
    attendance_notifications = models.BooleanField(default=True)
    trip_start_notifications = models.BooleanField(default=True)
    trip_end_notifications = models.BooleanField(default=True)
    delay_notifications = models.BooleanField(default=True)
    eta_notifications = models.BooleanField(default=True)
    emergency_notifications = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def is_quiet_time(self):
        """Check if current time is in quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        if not (self.quiet_hours_start and self.quiet_hours_end):
            return False
        
        current_time = timezone.now().time()
        
        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:  # Crosses midnight
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
    
    def should_send_notification(self, notification_type, channel):
        """Check if notification should be sent"""
        if self.is_quiet_time():
            return False
        
        # Check channel preference
        channel_enabled = {
            'push': self.enable_push,
            'email': self.enable_email,
            'sms': self.enable_sms,
            'in_app': self.enable_in_app,
        }.get(channel, False)
        
        if not channel_enabled:
            return False
        
        # Check notification type preference
        type_map = {
            'attendance': self.attendance_notifications,
            'trip_start': self.trip_start_notifications,
            'trip_end': self.trip_end_notifications,
            'delay': self.delay_notifications,
            'eta': self.eta_notifications,
            'emergency': self.emergency_notifications,
        }
        
        return type_map.get(notification_type, True)


class NotificationLog(models.Model):
    """Log of all notification attempts"""
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='logs',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        'authentication.User', 
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    
    channel = models.CharField(max_length=50, choices=NotificationChannel.choices)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('failed', 'Failed'),
            ('bounced', 'Bounced'),
        ]
    )
    
    # Details
    recipient = models.CharField(max_length=255)  # email, phone, etc
    message_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['channel', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.channel} - {self.status}"


class BulkNotification(models.Model):
    """For sending notifications to multiple users"""
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50, 
        choices=NotificationType.choices
    )
    
    # Recipients
    recipient_type = models.CharField(
        max_length=50,
        choices=[
            ('all_users', 'All Users'),
            ('all_parents', 'All Parents'),
            ('all_drivers', 'All Drivers'),
            ('specific_users', 'Specific Users'),
            ('by_class', 'By Class'),
            ('by_route', 'By Route'),
        ]
    )
    recipient_ids = models.JSONField(default=list, blank=True)
    
    # Channels
    send_push = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    send_in_app = models.BooleanField(default=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('sending', 'Sending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='draft'
    )
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.CASCADE,
        related_name='bulk_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bulk_notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient_type}"


class PushToken(models.Model):
    """Store FCM/device tokens for push notifications"""
    user = models.ForeignKey(
        'authentication.User', 
        on_delete=models.CASCADE, 
        related_name='push_tokens'
    )
    token = models.CharField(max_length=500, unique=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('android', 'Android'),
            ('ios', 'iOS'),
            ('web', 'Web'),
        ]
    )
    device_name = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'push_tokens'
        ordering = ['-last_used']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"