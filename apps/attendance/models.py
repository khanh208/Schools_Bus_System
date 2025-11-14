from django.contrib.gis.db import models
from django.utils import timezone
from django.db.models import Q


class AttendanceType(models.TextChoices):
    CHECK_IN = 'check_in', 'Check In'
    CHECK_OUT = 'check_out', 'Check Out'
    ABSENT = 'absent', 'Absent'


class AttendanceStatus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'
    EXCUSED = 'excused', 'Excused'


class Attendance(models.Model):
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
    
    # Check by
    checked_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_checks'
    )
    
    # Additional Info
    photo = models.ImageField(upload_to='attendance/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    temperature = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        blank=True, 
        null=True,
        help_text="Body temperature in Celsius"
    )
    
    # Notifications
    parent_notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-check_time']
        indexes = [
            models.Index(fields=['trip', 'student']),
            models.Index(fields=['check_time']),
            models.Index(fields=['status']),
        ]
        unique_together = [['trip', 'student', 'attendance_type']]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.attendance_type} - {self.status}"
    
    @property
    def is_on_time(self):
        """Check if student was checked in/out on time"""
        if not self.check_time or not self.stop:
            return None
        
        if self.attendance_type == AttendanceType.CHECK_IN:
            scheduled_time = self.stop.estimated_arrival
        else:
            scheduled_time = self.stop.estimated_departure
        
        if scheduled_time:
            check_time_only = self.check_time.time()
            time_diff = (
                timezone.datetime.combine(timezone.now().date(), check_time_only) -
                timezone.datetime.combine(timezone.now().date(), scheduled_time)
            ).total_seconds() / 60
            return abs(time_diff) <= 5  # Within 5 minutes
        return None
    
    def send_notification_to_parent(self):
        """Send notification to parent about attendance"""
        from apps.notifications.services import NotificationService
        
        if not self.parent_notified:
            NotificationService.send_attendance_notification(self)
            self.parent_notified = True
            self.notification_sent_at = timezone.now()
            self.save(update_fields=['parent_notified', 'notification_sent_at'])


class AttendanceException(models.Model):
    """Record for pre-planned absences or special circumstances"""
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='attendance_exceptions'
    )
    exception_type = models.CharField(
        max_length=50,
        choices=[
            ('sick_leave', 'Sick Leave'),
            ('vacation', 'Vacation'),
            ('family_emergency', 'Family Emergency'),
            ('other', 'Other'),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_exceptions'
    )
    supporting_document = models.FileField(
        upload_to='attendance_exceptions/', 
        blank=True, 
        null=True
    )
    
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.CASCADE,
        related_name='created_exceptions'
    )
    
    class Meta:
        db_table = 'attendance_exceptions'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.exception_type} ({self.start_date} to {self.end_date})"
    
    def is_valid_for_date(self, date):
        """Check if exception is valid for a given date"""
        return (
            self.is_approved and
            self.start_date <= date <= self.end_date
        )


class AttendanceReport(models.Model):
    """Daily/Weekly/Monthly attendance summary"""
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='attendance_reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Statistics
    total_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    late_days = models.IntegerField(default=0)
    excused_days = models.IntegerField(default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'attendance_reports'
        ordering = ['-start_date']
        unique_together = [['student', 'report_type', 'start_date', 'end_date']]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.report_type} ({self.start_date} to {self.end_date})"
    
    @classmethod
    def generate_report(cls, student, report_type, start_date, end_date):
        """Generate attendance report for a student"""
        attendances = Attendance.objects.filter(
            student=student,
            check_time__date__gte=start_date,
            check_time__date__lte=end_date,
            attendance_type=AttendanceType.CHECK_IN
        )
        
        total_days = (end_date - start_date).days + 1
        present_days = attendances.filter(status=AttendanceStatus.PRESENT).count()
        absent_days = attendances.filter(status=AttendanceStatus.ABSENT).count()
        late_days = attendances.filter(status=AttendanceStatus.LATE).count()
        excused_days = attendances.filter(status=AttendanceStatus.EXCUSED).count()
        
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        report, created = cls.objects.update_or_create(
            student=student,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            defaults={
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'excused_days': excused_days,
                'attendance_rate': attendance_rate,
            }
        )
        
        return report


class AttendanceAlert(models.Model):
    """Alerts for attendance issues"""
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='attendance_alerts'
    )
    alert_type = models.CharField(
        max_length=50,
        choices=[
            ('consecutive_absence', 'Consecutive Absence'),
            ('low_attendance_rate', 'Low Attendance Rate'),
            ('frequent_late', 'Frequent Late Arrivals'),
            ('missing_checkout', 'Missing Check-out'),
        ]
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    description = models.TextField()
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolution_notes = models.TextField(blank=True, null=True)
    
    # Notifications
    parent_notified = models.BooleanField(default=False)
    admin_notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance_alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert: {self.student.full_name} - {self.alert_type} ({self.severity})"
    
    @classmethod
    def check_and_create_alerts(cls, student):
        """Check student attendance and create alerts if needed"""
        from datetime import timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Check consecutive absences
        recent_attendances = Attendance.objects.filter(
            student=student,
            check_time__date__gte=week_ago,
            attendance_type=AttendanceType.CHECK_IN
        ).order_by('-check_time')
        
        consecutive_absences = 0
        for attendance in recent_attendances:
            if attendance.status == AttendanceStatus.ABSENT:
                consecutive_absences += 1
            else:
                break
        
        if consecutive_absences >= 3:
            cls.objects.get_or_create(
                student=student,
                alert_type='consecutive_absence',
                is_resolved=False,
                defaults={
                    'severity': 'high',
                    'description': f'Student has been absent for {consecutive_absences} consecutive days'
                }
            )
        
        # Check attendance rate
        month_ago = today - timedelta(days=30)
        monthly_attendances = Attendance.objects.filter(
            student=student,
            check_time__date__gte=month_ago,
            attendance_type=AttendanceType.CHECK_IN
        )
        
        total = monthly_attendances.count()
        present = monthly_attendances.filter(status=AttendanceStatus.PRESENT).count()
        
        if total > 0:
            rate = (present / total) * 100
            if rate < 80:
                cls.objects.get_or_create(
                    student=student,
                    alert_type='low_attendance_rate',
                    is_resolved=False,
                    defaults={
                        'severity': 'medium',
                        'description': f'Student attendance rate is {rate:.2f}% (below 80%)'
                    }
                )