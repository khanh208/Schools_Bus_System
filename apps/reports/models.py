from django.db import models
from django.utils import timezone


class DailyReport(models.Model):
    """Daily summary report"""
    report_date = models.DateField(unique=True, db_index=True)
    
    # Trip Statistics
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    cancelled_trips = models.IntegerField(default=0)
    in_progress_trips = models.IntegerField(default=0)
    
    # Attendance Statistics
    total_students_transported = models.IntegerField(default=0)
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    
    # Performance Metrics
    on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    late_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_delay_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Distance & Duration
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_duration_minutes = models.IntegerField(default=0)
    
    # Issues
    total_issues = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_reports'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Daily Report - {self.report_date}"
    
    @classmethod
    def generate_report(cls, date):
        """Generate daily report for a specific date"""
        from apps.tracking.models import Trip, TripStatus
        from apps.attendance.models import Attendance, AttendanceStatus
        from apps.tracking.models import TripIssue
        
        trips = Trip.objects.filter(trip_date=date)
        
        total_trips = trips.count()
        completed_trips = trips.filter(status=TripStatus.COMPLETED).count()
        cancelled_trips = trips.filter(status=TripStatus.CANCELLED).count()
        in_progress_trips = trips.filter(status=TripStatus.IN_PROGRESS).count()
        
        # Attendance
        attendances = Attendance.objects.filter(
            trip__trip_date=date,
            attendance_type='check_in'
        )
        
        total_students = attendances.count()
        present = attendances.filter(status=AttendanceStatus.PRESENT).count()
        absent = attendances.filter(status=AttendanceStatus.ABSENT).count()
        late = attendances.filter(status=AttendanceStatus.LATE).count()
        
        # Performance
        completed = trips.filter(status=TripStatus.COMPLETED)
        on_time = completed.filter(actual_start_time__lte=models.F('scheduled_start_time') + timezone.timedelta(minutes=5)).count()
        on_time_percentage = (on_time / completed.count() * 100) if completed.count() > 0 else 0
        late_percentage = 100 - on_time_percentage
        
        # Calculate average delay
        delays = []
        for trip in completed:
            if trip.delay:
                delays.append(trip.delay)
        average_delay = sum(delays) / len(delays) if delays else 0
        
        # Distance and duration
        total_distance = sum(trip.calculate_total_distance() for trip in completed)
        total_duration = sum(trip.duration or 0 for trip in completed)
        
        # Issues
        issues = TripIssue.objects.filter(trip__trip_date=date)
        total_issues = issues.count()
        critical_issues = issues.filter(severity='critical').count()
        
        report, created = cls.objects.update_or_create(
            report_date=date,
            defaults={
                'total_trips': total_trips,
                'completed_trips': completed_trips,
                'cancelled_trips': cancelled_trips,
                'in_progress_trips': in_progress_trips,
                'total_students_transported': total_students,
                'total_present': present,
                'total_absent': absent,
                'total_late': late,
                'on_time_percentage': on_time_percentage,
                'late_percentage': late_percentage,
                'average_delay_minutes': average_delay,
                'total_distance_km': total_distance,
                'total_duration_minutes': total_duration,
                'total_issues': total_issues,
                'critical_issues': critical_issues,
            }
        )
        
        return report


class TripPerformance(models.Model):
    """Performance metrics for individual trips"""
    trip = models.OneToOneField(
        'tracking.Trip', 
        on_delete=models.CASCADE, 
        related_name='performance'
    )
    
    # Duration
    scheduled_duration = models.IntegerField(null=True, blank=True, help_text="Minutes")
    actual_duration = models.IntegerField(null=True, blank=True, help_text="Minutes")
    delay_minutes = models.IntegerField(default=0)
    is_on_time = models.BooleanField(default=True)
    
    # Attendance
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Distance & Speed
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    average_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Stops
    stops_completed = models.IntegerField(default=0)
    stops_total = models.IntegerField(default=0)
    
    # Issues
    issues_reported = models.IntegerField(default=0)
    
    # Ratings
    driver_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    parent_feedback_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trip_performance'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Performance - {self.trip}"


class DriverPerformanceReport(models.Model):
    """Performance report for drivers"""
    driver = models.ForeignKey(
        'authentication.Driver', 
        on_delete=models.CASCADE, 
        related_name='performance_reports'
    )
    
    report_type = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Trip Statistics
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    cancelled_trips = models.IntegerField(default=0)
    
    # Performance
    on_time_trips = models.IntegerField(default=0)
    delayed_trips = models.IntegerField(default=0)
    on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_delay_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Distance
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_ratings = models.IntegerField(default=0)
    
    # Issues
    total_issues = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'driver_performance_reports'
        ordering = ['-start_date']
        unique_together = [['driver', 'report_type', 'start_date', 'end_date']]
    
    def __str__(self):
        return f"{self.driver.user.full_name} - {self.report_type} ({self.start_date})"


class RoutePerformanceReport(models.Model):
    """Performance report for routes"""
    route = models.ForeignKey(
        'routes.Route', 
        on_delete=models.CASCADE, 
        related_name='performance_reports'
    )
    
    report_type = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Trip Statistics
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    average_duration = models.IntegerField(default=0, help_text="Minutes")
    
    # Performance
    on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_delay_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Students
    average_students_per_trip = models.IntegerField(default=0)
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Distance
    average_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'route_performance_reports'
        ordering = ['-start_date']
        unique_together = [['route', 'report_type', 'start_date', 'end_date']]
    
    def __str__(self):
        return f"{self.route.route_code} - {self.report_type} ({self.start_date})"


class SystemStatistics(models.Model):
    """Overall system statistics"""
    date = models.DateField(unique=True)
    
    # Users
    total_users = models.IntegerField(default=0)
    active_parents = models.IntegerField(default=0)
    active_drivers = models.IntegerField(default=0)
    
    # Students
    total_students = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
    
    # Vehicles & Routes
    total_vehicles = models.IntegerField(default=0)
    active_vehicles = models.IntegerField(default=0)
    total_routes = models.IntegerField(default=0)
    active_routes = models.IntegerField(default=0)
    
    # Performance
    overall_on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_statistics'
        ordering = ['-date']
    
    def __str__(self):
        return f"System Stats - {self.date}"