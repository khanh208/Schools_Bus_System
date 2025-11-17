from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString
from django.core.validators import MinValueValidator
from django.utils import timezone


class VehicleStatus(models.TextChoices):
    ACTIVE = 'active', 'Đang hoạt động'
    MAINTENANCE = 'maintenance', 'Đang bảo trì'
    INACTIVE = 'inactive', 'Ngừng hoạt động'


class Vehicle(models.Model):
    plate_number = models.CharField('Biển số xe', max_length=20, unique=True)
    vehicle_type = models.CharField('Loại xe', max_length=50)
    capacity = models.IntegerField('Sức chứa', validators=[MinValueValidator(5)])
    model = models.CharField('Mẫu xe', max_length=100, blank=True, null=True)
    year = models.IntegerField('Năm sản xuất', blank=True, null=True)
    color = models.CharField('Màu sắc', max_length=50, blank=True, null=True)
    
    # Maintenance & Documents
    insurance_expiry = models.DateField('Ngày hết hạn bảo hiểm')
    registration_expiry = models.DateField('Ngày hết hạn đăng kiểm')
    last_maintenance = models.DateField('Bảo dưỡng lần cuối', blank=True, null=True)
    next_maintenance = models.DateField('Bảo dưỡng lần sau', blank=True, null=True)
    
    # GPS & Tracking
    gps_device_id = models.CharField('Mã thiết bị GPS', max_length=100, blank=True, null=True)
    
    # Status
    status = models.CharField(
        'Trạng thái',
        max_length=20, 
        choices=VehicleStatus.choices, 
        default=VehicleStatus.ACTIVE
    )
    is_active = models.BooleanField('Đang hoạt động', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Phương tiện'
        verbose_name_plural = 'Phương tiện'
        ordering = ['plate_number']
    
    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type})"
    @property
    def is_insurance_valid(self):
        return self.insurance_expiry > timezone.now().date()
    
    @property
    def is_registration_valid(self):
        return self.registration_expiry > timezone.now().date()
    
    @property
    def needs_maintenance(self):
        if self.next_maintenance:
            return self.next_maintenance <= timezone.now().date()
        return False
    
    @property
    def current_driver(self):
        """Get currently assigned driver"""
        from apps.authentication.models import Driver
        return Driver.objects.filter(vehicle=self).first()
    
    def can_operate(self):
        """Check if vehicle can operate"""
        return (
            self.is_active and 
            self.status == VehicleStatus.ACTIVE and
            self.is_insurance_valid and 
            self.is_registration_valid and 
            not self.needs_maintenance
        )


class RouteType(models.TextChoices):
    PICKUP = 'pickup', 'Đón học sinh'
    DROPOFF = 'dropoff', 'Trả học sinh'
    BOTH = 'both', 'Đón và trả'


class Route(models.Model):
    route_code = models.CharField('Mã tuyến', max_length=50, unique=True)
    route_name = models.CharField('Tên tuyến', max_length=255)
    description = models.TextField('Mô tả', blank=True, null=True)
    route_type = models.CharField('Loại tuyến', max_length=20, choices=RouteType.choices)
    
    # Relationships
    area = models.ForeignKey(
        'students.Area', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='routes',
        verbose_name='Khu vực'
    )
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='routes',
        verbose_name='Xe'
    )
    driver = models.ForeignKey(
        'authentication.Driver', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='routes',
        verbose_name='Tài xế'
    )
    
    # Route Details
    path = models.LineStringField('Đường đi', srid=4326, blank=True, null=True)
    estimated_duration = models.IntegerField('Thời gian dự kiến (phút)', blank=True, null=True)
    total_distance = models.DecimalField(
        'Tổng quãng đường (km)',
        max_digits=10, 
        decimal_places=2,
        blank=True, 
        null=True
    )
    
    # Status
    is_active = models.BooleanField('Đang hoạt động', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    
    class Meta:
        db_table = 'routes'
        verbose_name = 'Tuyến đường'
        verbose_name_plural = 'Tuyến đường'
        ordering = ['route_code']
    
    def __str__(self):
        return f"{self.route_code} - {self.route_name}"
    
    @property
    def stop_count(self):
        return self.stops.filter(is_active=True).count()
    
    @property
    def student_count(self):
        return self.student_assignments.filter(is_active=True).count()
    
    @property
    def is_fully_assigned(self):
        """Check if route has vehicle and driver assigned"""
        return self.vehicle is not None and self.driver is not None
    
    def get_ordered_stops(self):
        """Get stops in order"""
        return self.stops.filter(is_active=True).order_by('stop_order')


class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops', verbose_name='Tuyến đường')
    stop_order = models.IntegerField('Thứ tự điểm dừng')
    stop_name = models.CharField('Tên điểm dừng', max_length=255)
    location = models.PointField('Vị trí', srid=4326)
    address = models.TextField('Địa chỉ', blank=True, null=True)
    
    # Timing
    estimated_arrival = models.TimeField('Giờ đến dự kiến', blank=True, null=True)
    estimated_departure = models.TimeField('Giờ đi dự kiến', blank=True, null=True)
    stop_duration = models.IntegerField(
        'Thời gian dừng (phút)',
        default=2,
        validators=[MinValueValidator(1)]
    )
    
    # Status
    is_active = models.BooleanField('Đang hoạt động', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    
    class Meta:
        db_table = 'route_stops'
        verbose_name = 'Điểm dừng'
        verbose_name_plural = 'Điểm dừng'
        ordering = ['route', 'stop_order']
        unique_together = [['route', 'stop_order']]
    
    def __str__(self):
        return f"{self.route.route_code} - Điểm {self.stop_order}: {self.stop_name}"
    
    @property
    def student_count(self):
        """Count students assigned to this stop"""
        return self.student_assignments.filter(is_active=True).count()
    
    def get_coordinates(self):
        """Return location as [lng, lat]"""
        return [self.location.x, self.location.y]


class AssignmentType(models.TextChoices):
    PICKUP = 'pickup', 'Đón'
    DROPOFF = 'dropoff', 'Trả'
    BOTH = 'both', 'Cả hai'


class StudentRoute(models.Model):
    """Phân công học sinh vào tuyến & điểm dừng"""

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='route_assignments',
        verbose_name="Học sinh"
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='student_assignments',
        verbose_name="Tuyến xe"
    )
    stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name='student_assignments',
        verbose_name="Điểm đón/trả"
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        verbose_name="Loại phân công",
        help_text="Đón / Trả / Cả hai"
    )
    start_date = models.DateField(verbose_name="Ngày bắt đầu")
    end_date = models.DateField(blank=True, null=True, verbose_name="Ngày kết thúc")

    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = 'student_routes'
        verbose_name = "Phân công tuyến cho học sinh"
        verbose_name_plural = "Phân công tuyến cho học sinh"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['route', 'is_active']),
        ]

    def __str__(self):
        return f"{self.student.full_name} → {self.route.route_code} ({self.get_assignment_type_display()})"

    def is_valid_today(self):
        """Kiểm tra còn hiệu lực hôm nay hay không"""
        today = timezone.now().date()
        return (
            self.is_active and
            self.start_date <= today and
            (self.end_date is None or self.end_date >= today)
        )


class RouteSchedule(models.Model):
    """Lịch chạy xe theo ngày trong tuần"""

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules', verbose_name="Tuyến xe")

    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MinValueValidator(6)],
        help_text="0=Thứ 2, 6=Chủ nhật",
        verbose_name="Thứ trong tuần"
    )

    start_time = models.TimeField(verbose_name="Giờ bắt đầu")
    end_time = models.TimeField(blank=True, null=True, verbose_name="Giờ kết thúc")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động?")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = 'route_schedules'
        verbose_name = "Lịch chạy tuyến"
        verbose_name_plural = "Lịch chạy tuyến"
        ordering = ['route', 'day_of_week', 'start_time']
        unique_together = [['route', 'day_of_week', 'start_time']]

    def __str__(self):
        days = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        return f"{self.route.route_code} - {days[self.day_of_week]} lúc {self.start_time}"

    def is_today(self):
        """Có phải lịch ngày hôm nay không"""
        return timezone.now().weekday() == self.day_of_week


class VehicleMaintenance(models.Model):
    """Lịch sử bảo trì phương tiện"""

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        verbose_name="Xe"
    )

    maintenance_type = models.CharField(max_length=100, verbose_name="Loại bảo trì")
    description = models.TextField(verbose_name="Mô tả chi tiết")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Chi phí (VNĐ)"
    )
    performed_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Thực hiện bởi"
    )
    performed_at = models.DateTimeField(verbose_name="Ngày bảo trì")
    next_maintenance_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Lịch bảo trì tiếp theo"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú thêm")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Người tạo"
    )

    class Meta:
        db_table = 'vehicle_maintenance'
        verbose_name = "Bảo trì phương tiện"
        verbose_name_plural = "Bảo trì phương tiện"
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.maintenance_type} ({self.performed_at.date()})"
