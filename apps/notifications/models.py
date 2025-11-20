# apps/notifications/models.py - ĐƠN GIẢN
from django.db import models
from django.utils import timezone

class NotificationType(models.TextChoices):
    INFO = 'info', 'Information'
    WARNING = 'warning', 'Warning'
    ALERT = 'alert', 'Alert'
    SUCCESS = 'success', 'Success'

class Notification(models.Model):
    """Thông báo in-app cho phụ huynh"""
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
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """Cài đặt thông báo của user"""
    user = models.OneToOneField(
        'authentication.User', 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    enable_notifications = models.BooleanField(default=True)
    attendance_notifications = models.BooleanField(default=True)
    trip_notifications = models.BooleanField(default=True)
    eta_notifications = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
