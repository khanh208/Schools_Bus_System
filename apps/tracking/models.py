from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta


class TripType(models.TextChoices):
    MORNING_PICKUP = 'morning_pickup', 'Morning Pick Up'
    AFTERNOON_DROPOFF = 'afternoon_dropoff', 'Afternoon Drop Off'


class TripStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    DELAYED = 'delayed', 'Delayed'


class Trip(models.Model):
    route = models.ForeignKey(
        'routes.Route', 
        on_delete=models.CASCADE, 
        related_name='trips'
    )
    driver = models.ForeignKey(
        'authentication.Driver', 
        on_delete=models.CASCADE, 
        related_name='trips'
    )
    vehicle = models.ForeignKey(
        'routes.Vehicle', 
        on_delete=models.CASCADE, 
        related_name='trips'
    )
    
    # Trip Details
    trip_date = models.DateField()
    trip_type = models.CharField(max_length=20, choices=TripType.choices)
    
    # Timing
    scheduled_start_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    scheduled_end_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=TripStatus.choices, 
        default=TripStatus.SCHEDULED
    )
    
    # Statistics
    total_students = models.IntegerField(default=0)
    checked_in_students = models.IntegerField(default=0)
    checked_out_students = models.IntegerField(default=0)
    absent_students = models.IntegerField(default=0)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trips'
        verbose_name = 'Trip'
        verbose_name_plural = 'Trips'
        ordering = ['-trip_date', '-scheduled_start_time']
        indexes = [
            models.Index(fields=['trip_date', 'status']),
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['route', 'trip_date']),
        ]
    
    def __str__(self):
        return f"{self.route.route_code} - {self.trip_date} ({self.trip_type})"
    
    def start_trip(self):
        """Start the trip"""
        if self.status == TripStatus.SCHEDULED:
            self.status = TripStatus.IN_PROGRESS
            self.actual_start_time = timezone.now()
            self.save(update_fields=['status', 'actual_start_time'])
            
            # Update driver status
            self.driver.status = 'on_trip'
            self.driver.save(update_fields=['status'])
            
            # Gửi thông báo real-time
            from apps.notifications.realtime_service import RealtimeNotificationService
            RealtimeNotificationService.send_trip_update(
                self,
                f'Xe {self.vehicle.plate_number} đã bắt đầu chuyến đi lúc {self.actual_start_time.strftime("%H:%M")}'
            )
            
            return True
        return False

    def complete_trip(self):
        """Complete the trip"""
        if self.status == TripStatus.IN_PROGRESS:
            self.status = TripStatus.COMPLETED
            self.actual_end_time = timezone.now()
            self.save(update_fields=['status', 'actual_end_time'])
            
            # Update driver status
            self.driver.status = 'available'
            self.driver.save(update_fields=['status'])
            
            # Generate performance record
            self.calculate_performance()
            
            # Gửi thông báo real-time
            from apps.notifications.realtime_service import RealtimeNotificationService
            RealtimeNotificationService.send_trip_update(
                self,
                f'Chuyến đi đã hoàn thành lúc {self.actual_end_time.strftime("%H:%M")}'
            )
            
            return True
        return False
    
    def cancel_trip(self, reason):
        """Cancel the trip"""
        if self.status in [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]:
            self.status = TripStatus.CANCELLED
            self.cancellation_reason = reason
            self.save(update_fields=['status', 'cancellation_reason'])
            
            if self.driver.status == 'on_trip':
                self.driver.status = 'available'
                self.driver.save(update_fields=['status'])
            
            return True
        return False
    
    @property
    def duration(self):
        """Calculate actual trip duration in minutes"""
        if self.actual_start_time and self.actual_end_time:
            return (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        return None
    
    @property
    def delay(self):
        """Calculate delay in minutes"""
        if self.actual_start_time and self.scheduled_start_time:
            return (self.actual_start_time - self.scheduled_start_time).total_seconds() / 60
        return None
    
    @property
    def is_delayed(self):
        """Check if trip is delayed (more than 5 minutes)"""
        delay = self.delay
        return delay > 5 if delay else False
    
    @property
    def attendance_rate(self):
        """Calculate attendance rate"""
        if self.total_students > 0:
            return (self.checked_in_students / self.total_students) * 100
        return 0
    
    @property
    def current_location(self):
        """Get the most recent location of the trip"""
        latest_log = self.location_logs.order_by('-timestamp').first()
        return latest_log.location if latest_log else None
    
    def calculate_performance(self):
        """Calculate and save trip performance metrics"""
        from apps.reports.models import TripPerformance
        
        if self.status == TripStatus.COMPLETED:
            scheduled_duration = None
            if self.scheduled_end_time and self.scheduled_start_time:
                scheduled_duration = (
                    self.scheduled_end_time - self.scheduled_start_time
                ).total_seconds() / 60
            
            actual_duration = self.duration
            delay_minutes = self.delay or 0
            
            # Calculate distance from location logs
            total_distance = self.calculate_total_distance()
            
            # Average speed
            average_speed = None
            if actual_duration and total_distance:
                average_speed = (total_distance / actual_duration) * 60  # km/h
            
            TripPerformance.objects.update_or_create(
                trip=self,
                defaults={
                    'scheduled_duration': scheduled_duration,
                    'actual_duration': actual_duration,
                    'delay_minutes': delay_minutes,
                    'is_on_time': delay_minutes <= 5,
                    'attendance_rate': self.attendance_rate,
                    'distance_km': total_distance,
                    'average_speed': average_speed,
                    'stops_completed': self.stop_arrivals.count(),
                }
            )
    
    def calculate_total_distance(self):
        """Calculate total distance traveled from GPS logs"""
        from django.contrib.gis.db.models.functions import Distance
        
        logs = self.location_logs.order_by('timestamp')
        total_distance = 0
        
        previous_location = None
        for log in logs:
            if previous_location:
                distance = previous_location.distance(log.location) * 111  # Convert to km
                total_distance += distance
            previous_location = log.location
        
        return round(total_distance, 2)
    
    def get_eta_for_stop(self, stop):
        """Calculate ETA for a specific stop"""
        from apps.tracking.services import ETAService
        
        if self.status == TripStatus.IN_PROGRESS:
            return ETAService.calculate_eta(self, stop)
        return None


class LocationLog(models.Model):
    """GPS tracking log for trips"""
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.CASCADE, 
        related_name='location_logs'
    )
    driver = models.ForeignKey(
        'authentication.Driver', 
        on_delete=models.CASCADE, 
        related_name='location_logs'
    )
    
    # Location Data
    location = models.PointField(srid=4326)
    accuracy = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="GPS accuracy in meters",
        null=True,
        blank=True
    )
    
    # Movement Data
    speed = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Speed in km/h"
    )
    heading = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Direction in degrees (0-360)"
    )
    altitude = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Altitude in meters"
    )
    
    # Device Info
    battery_level = models.IntegerField(null=True, blank=True)
    is_online = models.BooleanField(default=True)
    
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'location_logs'
        verbose_name = 'Location Log'
        verbose_name_plural = 'Location Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['trip', 'timestamp']),
            models.Index(fields=['driver', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.trip} - {self.timestamp}"
    
    @property
    def coordinates(self):
        """Return coordinates as [lng, lat]"""
        return [self.location.x, self.location.y]
    
    def distance_to(self, point):
        """Calculate distance to another point in kilometers"""
        if isinstance(point, Point):
            return self.location.distance(point) * 111
        return None


class StopArrival(models.Model):
    """Record of when the vehicle arrives at each stop"""
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.CASCADE, 
        related_name='stop_arrivals'
    )
    stop = models.ForeignKey(
        'routes.RouteStop', 
        on_delete=models.CASCADE, 
        related_name='arrivals'
    )
    
    scheduled_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    
    location = models.PointField(srid=4326, null=True, blank=True)
    
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
        """Calculate delay in minutes"""
        if self.actual_arrival and self.scheduled_arrival:
            return (self.actual_arrival - self.scheduled_arrival).total_seconds() / 60
        return None
    
    @property
    def is_on_time(self):
        """Check if arrival was on time (within 5 minutes)"""
        delay = self.delay_minutes
        return abs(delay) <= 5 if delay is not None else None
    
    @property
    def dwell_time(self):
        """Calculate how long the vehicle stayed at the stop"""
        if self.actual_arrival and self.departure_time:
            return (self.departure_time - self.actual_arrival).total_seconds() / 60
        return None


class TripIssue(models.Model):
    """Issues or incidents during trips"""
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.CASCADE, 
        related_name='issues'
    )
    issue_type = models.CharField(
        max_length=50,
        choices=[
            ('vehicle_breakdown', 'Vehicle Breakdown'),
            ('traffic_jam', 'Traffic Jam'),
            ('weather', 'Weather Issue'),
            ('student_incident', 'Student Incident'),
            ('accident', 'Accident'),
            ('other', 'Other'),
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
    location = models.PointField(srid=4326, null=True, blank=True)
    
    reported_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.CASCADE,
        related_name='reported_issues'
    )
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    # Media
    photo = models.ImageField(upload_to='trip_issues/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trip_issues'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.trip} - {self.issue_type} ({self.severity})"


class ETARecord(models.Model):
    """Historical ETA calculations for analysis"""
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.CASCADE, 
        related_name='eta_records'
    )
    stop = models.ForeignKey(
        'routes.RouteStop', 
        on_delete=models.CASCADE, 
        related_name='eta_records'
    )
    
    calculated_at = models.DateTimeField(auto_now_add=True)
    estimated_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    distance_remaining = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Distance in kilometers"
    )
    estimated_time_minutes = models.IntegerField()
    
    # Accuracy metrics
    prediction_error_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'eta_records'
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"ETA for {self.stop.stop_name} at {self.calculated_at}"
    
    def calculate_accuracy(self):
        """Calculate prediction accuracy when actual arrival is known"""
        if self.actual_arrival:
            predicted = self.estimated_arrival
            actual = self.actual_arrival
            error = (actual - predicted).total_seconds() / 60
            self.prediction_error_minutes = int(error)
            self.save(update_fields=['prediction_error_minutes'])