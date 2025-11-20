# ============================================
# apps/attendance/models.py - SIMPLIFIED
# ============================================

from django.contrib.gis.db import models
from django.utils import timezone


class AttendanceType(models.TextChoices):
    CHECK_IN = 'check_in', 'Check In'
    CHECK_OUT = 'check_out', 'Check Out'
    ABSENT = 'absent', 'Absent'


class AttendanceStatus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'


class Attendance(models.Model):
    """Simple attendance tracking"""
    trip = models.ForeignKey(
        'tracking.Trip', 
        on_delete=models.CASCADE, 
        related_name='attendances'
    )
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='attendances'
    )
    stop = models.ForeignKey(
        'routes.RouteStop', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances'
    )
    
    # Attendance Details
    attendance_type = models.CharField(max_length=20, choices=AttendanceType.choices)
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices)
    check_time = models.DateTimeField(null=True, blank=True)
    location = models.PointField(srid=4326, null=True, blank=True)
    
    # Checked by
    checked_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_checks'
    )
    
    # Additional Info
    notes = models.TextField(blank=True, null=True)
    temperature = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        blank=True, 
        null=True
    )
    
    # Notification sent
    parent_notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        ordering = ['-check_time']
        unique_together = [['trip', 'student', 'attendance_type']]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.attendance_type} - {self.status}"
    
    def send_notification_to_parent(self):
        """Send simple notification to parent"""
        from apps.notifications.models import Notification
        
        if not self.parent_notified:
            Notification.objects.create(
                user=self.student.parent.user,
                title=f"Điểm danh: {self.student.full_name}",
                message=f"Con em {self.get_status_display()} lúc {self.check_time.strftime('%H:%M')}",
                notification_type='info'
            )
            
            self.parent_notified = True
            self.save(update_fields=['parent_notified'])
