# ============================================
# apps/tracking/models.py - SIMPLIFIED
# ============================================

from django.contrib.gis.db import models
from django.utils import timezone
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
    """Simple trip tracking"""
    route = models.ForeignKey('routes.Route', on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey('authentication.Driver', on_delete=models.CASCADE, related_name='trips')
    vehicle = models.ForeignKey('routes.Vehicle', on_delete=models.CASCADE, related_name='trips')
    
    trip_date = models.DateField()
    trip_type = models.CharField(max_length=20, choices=TripType.choices)
    
    # Timing
    scheduled_start_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    scheduled_end_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.SCHEDULED)
    
    # Statistics
    total_students = models.IntegerField(default=0)
    checked_in_students = models.IntegerField(default=0)
    checked_out_students = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trips'
        ordering = ['-trip_date', '-scheduled_start_time']
    
    def __str__(self):
        return f"{self.route.route_code} - {self.trip_date}"
    
    def start_trip(self):
        if self.status == TripStatus.SCHEDULED:
            self.status = TripStatus.IN_PROGRESS
            self.actual_start_time = timezone.now()
            self.save(update_fields=['status', 'actual_start_time'])
            
            self.driver.status = 'on_trip'
            self.driver.save(update_fields=['status'])
            return True
        return False
    
    def complete_trip(self):
        if self.status == TripStatus.IN_PROGRESS:
            self.status = TripStatus.COMPLETED
            self.actual_end_time = timezone.now()
            self.save(update_fields=['status', 'actual_end_time'])
            
            self.driver.status = 'available'
            self.driver.save(update_fields=['status'])
            return True
        return False
    
    @property
    def duration(self):
        if self.actual_start_time and self.actual_end_time:
            return (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        return None
    
    @property
    def delay(self):
        if self.actual_start_time and self.scheduled_start_time:
            return (self.actual_start_time - self.scheduled_start_time).total_seconds() / 60
        return None
    
    @property
    def is_on_time(self):
        delay = self.delay
        return delay <= 5 if delay else True


class LocationLog(models.Model):
    """GPS tracking"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='location_logs')
    driver = models.ForeignKey('authentication.Driver', on_delete=models.CASCADE)
    
    location = models.PointField(srid=4326)
    speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    timestamp = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'location_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.trip} - {self.timestamp}"


class StopArrival(models.Model):
    """Stop arrival tracking"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stop_arrivals')
    stop = models.ForeignKey('routes.RouteStop', on_delete=models.CASCADE)
    
    scheduled_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    students_boarded = models.IntegerField(default=0)
    students_alighted = models.IntegerField(default=0)
    
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