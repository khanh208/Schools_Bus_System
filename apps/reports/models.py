# apps/reports/models.py
from django.db import models
from django.utils import timezone

class DailyReport(models.Model):
    """Báo cáo tổng hợp hàng ngày"""
    report_date = models.DateField(unique=True, db_index=True)
    
    # Thống kê chuyến đi
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    cancelled_trips = models.IntegerField(default=0)
    in_progress_trips = models.IntegerField(default=0)
    
    # Thống kê vận chuyển
    total_students_transported = models.IntegerField(default=0)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_duration_minutes = models.IntegerField(default=0)
    
    # Thống kê điểm danh
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    
    # Chỉ số hiệu suất
    on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    late_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_delay_minutes = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Vấn đề
    total_issues = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_reports'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Daily Report - {self.report_date}"


class TripPerformance(models.Model):
    """Đánh giá hiệu suất chuyến đi"""
    trip = models.OneToOneField(
        'tracking.Trip', 
        on_delete=models.CASCADE, 
        related_name='performance'
    )
    
    # Thời gian
    scheduled_duration = models.IntegerField(null=True, blank=True)  # phút
    actual_duration = models.IntegerField(null=True, blank=True)  # phút
    delay_minutes = models.IntegerField(default=0)
    is_on_time = models.BooleanField(default=True)
    
    # Điểm danh & Vận hành
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    average_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Stops
    stops_completed = models.IntegerField(default=0)
    stops_total = models.IntegerField(default=0)
    
    # Feedback & Issues
    issues_reported = models.IntegerField(default=0)
    driver_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    parent_feedback_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trip_performance'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Performance - {self.trip}"


class DriverPerformanceReport(models.Model):
    """Báo cáo hiệu suất tài xế"""
    driver = models.ForeignKey('authentication.Driver', on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=[
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ])
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Stats
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    cancelled_trips = models.IntegerField(default=0)
    
    on_time_trips = models.IntegerField(default=0)
    delayed_trips = models.IntegerField(default=0)
    on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_delay_minutes = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Rating
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_ratings = models.IntegerField(default=0)
    
    # Safety
    total_issues = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'driver_performance_reports'
        ordering = ['-start_date']


class RoutePerformanceReport(models.Model):
    """Báo cáo hiệu suất tuyến đường"""
    route = models.ForeignKey('routes.Route', on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=[
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ])
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    
    average_duration = models.IntegerField(default=0)  # minutes
    on_time_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_delay_minutes = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    average_students_per_trip = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'route_performance_reports'
        ordering = ['-start_date']


class SystemStatistics(models.Model):
    """Thống kê toàn hệ thống (Snapshot)"""
    date = models.DateField(unique=True, db_index=True)
    
    # Users
    total_users = models.IntegerField(default=0)
    active_parents = models.IntegerField(default=0)
    active_drivers = models.IntegerField(default=0)
    
    # Entities
    total_students = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
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