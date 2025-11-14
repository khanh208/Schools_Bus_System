from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString
from django.core.validators import MinValueValidator
from django.utils import timezone


class VehicleStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    MAINTENANCE = 'maintenance', 'Under Maintenance'
    INACTIVE = 'inactive', 'Inactive'


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50)  # bus, van, etc
    capacity = models.IntegerField(validators=[MinValueValidator(5)])
    model = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    
    # Maintenance & Documents
    insurance_expiry = models.DateField()
    registration_expiry = models.DateField()
    last_maintenance = models.DateField(blank=True, null=True)
    next_maintenance = models.DateField(blank=True, null=True)
    
    # GPS & Tracking
    gps_device_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=VehicleStatus.choices, 
        default=VehicleStatus.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
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
    PICKUP = 'pickup', 'Pick Up'
    DROPOFF = 'dropoff', 'Drop Off'
    BOTH = 'both', 'Both'


class Route(models.Model):
    route_code = models.CharField(max_length=50, unique=True)
    route_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    route_type = models.CharField(max_length=20, choices=RouteType.choices)
    
    # Relationships
    area = models.ForeignKey(
        'students.Area', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='routes'
    )
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='routes'
    )
    driver = models.ForeignKey(
        'authentication.Driver', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='routes'
    )
    
    # Route Details
    path = models.LineStringField(srid=4326, blank=True, null=True)
    estimated_duration = models.IntegerField(help_text="Duration in minutes", blank=True, null=True)
    total_distance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Distance in kilometers",
        blank=True, 
        null=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'routes'
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
        ordering = ['route_code']
        indexes = [
            models.Index(fields=['route_code']),
            models.Index(fields=['is_active']),
        ]
    
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
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_order = models.IntegerField()
    stop_name = models.CharField(max_length=255)
    location = models.PointField(srid=4326)
    address = models.TextField(blank=True, null=True)
    
    # Timing
    estimated_arrival = models.TimeField(blank=True, null=True)
    estimated_departure = models.TimeField(blank=True, null=True)
    stop_duration = models.IntegerField(
        default=2, 
        help_text="Duration in minutes",
        validators=[MinValueValidator(1)]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'route_stops'
        verbose_name = 'Route Stop'
        verbose_name_plural = 'Route Stops'
        ordering = ['route', 'stop_order']
        unique_together = [['route', 'stop_order']]
        indexes = [
            models.Index(fields=['route', 'stop_order']),
        ]
    
    def __str__(self):
        return f"{self.route.route_code} - Stop {self.stop_order}: {self.stop_name}"
    
    @property
    def student_count(self):
        """Count students assigned to this stop"""
        return self.student_assignments.filter(is_active=True).count()
    
    def get_coordinates(self):
        """Return location as [lng, lat]"""
        return [self.location.x, self.location.y]


class AssignmentType(models.TextChoices):
    PICKUP = 'pickup', 'Pick Up'
    DROPOFF = 'dropoff', 'Drop Off'
    BOTH = 'both', 'Both'


class StudentRoute(models.Model):
    """Assignment of students to routes and stops"""
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='route_assignments'
    )
    route = models.ForeignKey(
        Route, 
        on_delete=models.CASCADE, 
        related_name='student_assignments'
    )
    stop = models.ForeignKey(
        RouteStop, 
        on_delete=models.CASCADE, 
        related_name='student_assignments'
    )
    
    assignment_type = models.CharField(max_length=20, choices=AssignmentType.choices)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_routes'
        verbose_name = 'Student Route Assignment'
        verbose_name_plural = 'Student Route Assignments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['route', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} -> {self.route.route_code} ({self.assignment_type})"
    
    def is_valid_today(self):
        """Check if assignment is valid for today"""
        today = timezone.now().date()
        return (
            self.is_active and
            self.start_date <= today and
            (self.end_date is None or self.end_date >= today)
        )


class RouteSchedule(models.Model):
    """Schedule for routes by day of week"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MinValueValidator(6)],
        help_text="0=Monday, 6=Sunday"
    )
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'route_schedules'
        verbose_name = 'Route Schedule'
        verbose_name_plural = 'Route Schedules'
        ordering = ['route', 'day_of_week', 'start_time']
        unique_together = [['route', 'day_of_week', 'start_time']]
    
    def __str__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"{self.route.route_code} - {days[self.day_of_week]} at {self.start_time}"
    
    def is_today(self):
        """Check if this schedule is for today"""
        return timezone.now().weekday() == self.day_of_week


class VehicleMaintenance(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=100)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    performed_by = models.CharField(max_length=255, blank=True, null=True)
    performed_at = models.DateTimeField()
    next_maintenance_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'vehicle_maintenance'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.maintenance_type} ({self.performed_at.date()})"