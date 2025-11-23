# apps/tracking/models.py - FIXED VERSION
from django.contrib.gis.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta


class TripType(models.TextChoices):
    MORNING_PICKUP = 'morning_pickup', 'Morning Pick Up'
    AFTERNOON_DROPOFF = 'afternoon_dropoff', 'Afternoon Drop Off'


class TripStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Trip(models.Model):
    """Chuyến đi - Đã fix validation và logic"""
    route = models.ForeignKey(
        'routes.Route', 
        on_delete=models.CASCADE, 
        related_name='trips',
        help_text="Tuyến đường của chuyến đi"
    )
    driver = models.ForeignKey(
        'authentication.Driver', 
        on_delete=models.CASCADE, 
        related_name='trips',
        help_text="Tài xế phụ trách"
    )
    vehicle = models.ForeignKey(
        'routes.Vehicle', 
        on_delete=models.CASCADE, 
        related_name='trips',
        help_text="Xe thực hiện chuyến"
    )
    
    trip_date = models.DateField(db_index=True)
    trip_type = models.CharField(max_length=20, choices=TripType.choices)
    
    # Timing
    scheduled_start_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    scheduled_end_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=TripStatus.choices, 
        default=TripStatus.SCHEDULED,
        db_index=True
    )
    
    # Statistics
    total_students = models.IntegerField(default=0)
    checked_in_students = models.IntegerField(default=0)
    checked_out_students = models.IntegerField(default=0)
    absent_students = models.IntegerField(default=0)  # ✅ THÊM FIELD NÀY
    
    notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)  # ✅ THÊM FIELD
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trips'
        ordering = ['-trip_date', '-scheduled_start_time']
        # ✅ THÊM CONSTRAINT: Không cho 1 xe/tài xế chạy 2 chuyến cùng lúc
        constraints = [
            models.UniqueConstraint(
                fields=['vehicle', 'trip_date', 'trip_type'],
                condition=models.Q(status__in=['scheduled', 'in_progress']),
                name='unique_vehicle_per_trip'
            ),
            models.UniqueConstraint(
                fields=['driver', 'trip_date', 'trip_type'],
                condition=models.Q(status__in=['scheduled', 'in_progress']),
                name='unique_driver_per_trip'
            )
        ]
        indexes = [
            models.Index(fields=['trip_date', 'status']),
            models.Index(fields=['route', 'trip_date']),
        ]
    
    def __str__(self):
        return f"{self.route.route_code} - {self.trip_date} ({self.get_trip_type_display()})"
    
    def clean(self):
        """✅ Validation logic"""
        # 1. Kiểm tra xe phải khớp với tuyến
        if self.vehicle and self.route.vehicle and self.vehicle != self.route.vehicle:
            raise ValidationError({
                'vehicle': 'Xe không khớp với xe đã gán cho tuyến đường.'
            })
        
        # 2. Kiểm tra tài xế phải khớp với tuyến
        if self.driver and self.route.driver and self.driver != self.route.driver:
            raise ValidationError({
                'driver': 'Tài xế không khớp với tài xế đã gán cho tuyến đường.'
            })
        
        # 3. Kiểm tra scheduled_end_time > scheduled_start_time
        if self.scheduled_end_time and self.scheduled_start_time:
            if self.scheduled_end_time <= self.scheduled_start_time:
                raise ValidationError({
                    'scheduled_end_time': 'Thời gian kết thúc phải sau thời gian bắt đầu.'
                })
    
    def start_trip(self):
        """✅ Bắt đầu chuyến đi với validation"""
        if self.status != TripStatus.SCHEDULED:
            return False, f"Chuyến đi đang ở trạng thái {self.get_status_display()}"
        
        # Kiểm tra xe còn hoạt động không
        if not self.vehicle.can_operate():
            return False, "Xe không thể hoạt động (bảo trì/hết hạn giấy tờ)"
        
        # Kiểm tra tài xế available
        if self.driver.status != 'available':
            return False, f"Tài xế đang {self.driver.get_status_display()}"
        
        self.status = TripStatus.IN_PROGRESS
        self.actual_start_time = timezone.now()
        self.save(update_fields=['status', 'actual_start_time', 'updated_at'])
        
        # Cập nhật trạng thái tài xế
        self.driver.status = 'on_trip'
        self.driver.save(update_fields=['status'])
        
        return True, "Bắt đầu chuyến đi thành công"
    
    def complete_trip(self):
        """✅ Kết thúc chuyến đi"""
        if self.status != TripStatus.IN_PROGRESS:
            return False, "Chuyến đi không ở trạng thái đang chạy"
        
        self.status = TripStatus.COMPLETED
        self.actual_end_time = timezone.now()
        self.save(update_fields=['status', 'actual_end_time', 'updated_at'])
        
        # Cập nhật trạng thái tài xế
        self.driver.status = 'available'
        self.driver.save(update_fields=['status'])
        
        # ✅ Tạo báo cáo hiệu suất
        self._generate_performance_report()
        
        return True, "Hoàn thành chuyến đi"
    
    def cancel_trip(self, reason=""):
        """✅ Hủy chuyến đi"""
        if self.status in [TripStatus.COMPLETED, TripStatus.CANCELLED]:
            return False, f"Không thể hủy chuyến đã {self.get_status_display()}"
        
        self.status = TripStatus.CANCELLED
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
        
        # Reset trạng thái tài xế nếu đang chạy
        if self.driver.status == 'on_trip':
            self.driver.status = 'available'
            self.driver.save(update_fields=['status'])
        
        return True, "Đã hủy chuyến đi"
    
    def _generate_performance_report(self):
        """Tạo báo cáo hiệu suất sau khi hoàn thành"""
        from apps.reports.models import TripPerformance
        
        TripPerformance.objects.create(
            trip=self,
            scheduled_duration=self.duration_scheduled,
            actual_duration=self.duration,
            delay_minutes=self.delay,
            is_on_time=self.is_on_time,
            attendance_rate=self.attendance_rate,
            stops_completed=self.stops_completed,
            stops_total=self.route.stop_count
        )
    
    @property
    def duration(self):
        """Thời gian thực tế (phút)"""
        if self.actual_start_time and self.actual_end_time:
            return (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        return None
    
    @property
    def duration_scheduled(self):
        """Thời gian dự kiến (phút)"""
        if self.scheduled_start_time and self.scheduled_end_time:
            return (self.scheduled_end_time - self.scheduled_start_time).total_seconds() / 60
        return None
    
    @property
    def delay(self):
        """Độ trễ (phút)"""
        if self.actual_start_time and self.scheduled_start_time:
            return (self.actual_start_time - self.scheduled_start_time).total_seconds() / 60
        return None
    
    @property
    def is_on_time(self):
        """Có đúng giờ không (delay <= 5 phút)"""
        delay = self.delay
        return delay is not None and delay <= 5
    
    @property
    def attendance_rate(self):
        """Tỷ lệ điểm danh (%)"""
        if self.total_students == 0:
            return 0
        return round((self.checked_in_students / self.total_students) * 100, 1)
    
    @property
    def stops_completed(self):
        """Số điểm dừng đã hoàn thành"""
        from apps.tracking.models import StopArrival
        return StopArrival.objects.filter(
            trip=self,
            actual_arrival__isnull=False
        ).count()


class LocationLog(models.Model):
    """GPS tracking - Đã tối ưu"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='location_logs')
    driver = models.ForeignKey('authentication.Driver', on_delete=models.CASCADE)
    
    location = models.PointField(srid=4326)
    speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    heading = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accuracy = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True)
    
    class Meta:
        db_table = 'location_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['trip', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.trip} @ {self.timestamp}"


class StopArrival(models.Model):
    """Điểm dừng - Tracking khi xe đến"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stop_arrivals')
    stop = models.ForeignKey('routes.RouteStop', on_delete=models.CASCADE)
    
    scheduled_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)  # ✅ THÊM
    
    students_boarded = models.IntegerField(default=0)
    students_alighted = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stop_arrivals'
        ordering = ['scheduled_arrival']
        unique_together = [['trip', 'stop']]
    
    def __str__(self):
        return f"{self.trip} - {self.stop.stop_name}"
    
    @property
    def delay_minutes(self):
        if self.actual_arrival and self.scheduled_arrival:
            return (self.actual_arrival - self.scheduled_arrival).total_seconds() / 60
        return None
    
    @property
    def dwell_time(self):
        """Thời gian dừng tại điểm (phút)"""
        if self.actual_arrival and self.actual_departure:
            return (self.actual_departure - self.actual_arrival).total_seconds() / 60
        return None


class ETARecord(models.Model):
    """✅ THÊM MODEL MỚI: Lưu lịch sử ETA predictions"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='eta_records')
    stop = models.ForeignKey('routes.RouteStop', on_delete=models.CASCADE)
    
    estimated_arrival = models.DateTimeField()
    distance_remaining = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_time_minutes = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eta_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trip', 'stop', '-created_at']),
        ]
