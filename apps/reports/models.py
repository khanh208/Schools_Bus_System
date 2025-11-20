# apps/reports/models.py - ĐƠN GIẢN
from django.db import models
from django.utils import timezone

class DailyReport(models.Model):
    """Báo cáo tổng hợp hàng ngày"""
    report_date = models.DateField(unique=True, db_index=True)
    
    # Thống kê chuyến đi
    total_trips = models.IntegerField(default=0)
    completed_trips = models.IntegerField(default=0)
    
    # Thống kê điểm danh
    total_students = models.IntegerField(default=0)
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    
    # Thống kê đúng giờ
    on_time_trips = models.IntegerField(default=0)
    delayed_trips = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_reports'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Daily Report - {self.report_date}"
    
    @property
    def attendance_rate(self):
        if self.total_students > 0:
            return (self.total_present / self.total_students) * 100
        return 0
    
    @property
    def on_time_rate(self):
        if self.total_trips > 0:
            return (self.on_time_trips / self.total_trips) * 100
        return 0


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
    
    # Điểm danh
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Quãng đường
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trip_performance'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Performance - {self.trip}"
