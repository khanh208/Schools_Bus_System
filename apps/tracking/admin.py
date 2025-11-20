# apps/tracking/admin.py
from django.contrib import admin
from .models import Trip, LocationLog, StopArrival


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'route', 'trip_date', 'trip_type', 'status']
    list_filter = ['trip_date', 'trip_type', 'status', 'route']
    search_fields = ['route__route_code', 'route__route_name']
    ordering = ['-trip_date', 'trip_type']


@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):
    """
    Admin đơn giản cho LocationLog – chỉ dùng field chắc chắn có:
    - trip: FK
    - driver: FK
    - timestamp: DateTime
    """
    list_display = ['id', 'trip', 'driver', 'timestamp']
    list_filter = ['trip', 'driver']
    search_fields = [
        'trip__route__route_code',
        'trip__route__route_name',
        'driver__user__full_name',
    ]
    ordering = ['-timestamp']
    # ❌ KHÔNG dùng readonly_fields, battery_level, is_online, ... nữa


@admin.register(StopArrival)
class StopArrivalAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip', 'stop', 'actual_arrival', 'created_at']
    list_filter = ['trip', 'stop']
    search_fields = ['trip__route__route_code', 'stop__stop_name']
    ordering = ['-actual_arrival', '-created_at']
