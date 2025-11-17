from django.contrib import admin
from django.utils.html import format_html
from .models import Trip, LocationLog, StopArrival, TripIssue

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['get_route', 'trip_date', 'get_trip_type', 'get_status', 'get_driver', 'get_attendance']
    list_filter = ['status', 'trip_type', 'trip_date']
    search_fields = ['route__route_code', 'driver__user__full_name']
    ordering = ['-trip_date', '-scheduled_start_time']
    date_hierarchy = 'trip_date'
    
    fieldsets = (
        ('Thông tin chuyến đi', {
            'fields': ('route', 'driver', 'vehicle', 'trip_date', 'trip_type')
        }),
        ('Thời gian', {
            'fields': ('scheduled_start_time', 'actual_start_time', 'scheduled_end_time', 'actual_end_time')
        }),
        ('Điểm danh', {
            'fields': ('total_students', 'checked_in_students', 'checked_out_students', 'absent_students')
        }),
        ('Trạng thái', {
            'fields': ('status',)
        }),
        ('Ghi chú', {
            'fields': ('notes', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_route(self, obj):
        return f"{obj.route.route_code} - {obj.route.route_name}"
    get_route.short_description = 'Tuyến đường'
    
    def get_trip_type(self, obj):
        colors = {
            'morning_pickup': '#ffc107',
            'afternoon_dropoff': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.trip_type, '#000'),
            obj.get_trip_type_display()
        )
    get_trip_type.short_description = 'Loại chuyến'
    
    def get_status(self, obj):
        colors = {
            'scheduled': '#6c757d',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'delayed': '#ffc107'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    get_status.short_description = 'Trạng thái'
    
    def get_driver(self, obj):
        return obj.driver.user.full_name
    get_driver.short_description = 'Tài xế'
    
    def get_attendance(self, obj):
        if obj.total_students > 0:
            rate = (obj.checked_in_students / obj.total_students) * 100
            color = 'green' if rate >= 90 else 'orange' if rate >= 70 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{} ({:.1f}%)</span>',
                color,
                obj.checked_in_students,
                obj.total_students,
                rate
            )
        return '0/0'
    get_attendance.short_description = 'Điểm danh'

@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):
    list_display = ['get_trip', 'get_driver', 'timestamp', 'get_speed', 'battery_level', 'is_online']
    list_filter = ['is_online', 'timestamp']
    search_fields = ['trip__route__route_code', 'driver__user__full_name']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Thông tin', {
            'fields': ('trip', 'driver', 'location', 'timestamp')
        }),
        ('Dữ liệu GPS', {
            'fields': ('speed', 'heading', 'altitude', 'accuracy')
        }),
        ('Thiết bị', {
            'fields': ('battery_level', 'is_online')
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_trip(self, obj):
        return f"{obj.trip.route.route_code} - {obj.trip.trip_date}"
    get_trip.short_description = 'Chuyến đi'
    
    def get_driver(self, obj):
        return obj.driver.user.full_name
    get_driver.short_description = 'Tài xế'
    
    def get_speed(self, obj):
        if obj.speed:
            return f"{obj.speed:.1f} km/h"
        return "0 km/h"
    get_speed.short_description = 'Tốc độ'

@admin.register(StopArrival)
class StopArrivalAdmin(admin.ModelAdmin):
    list_display = ['get_trip', 'get_stop', 'scheduled_arrival', 'actual_arrival', 'get_delay', 'get_students']
    list_filter = ['trip__trip_date', 'stop__route']
    search_fields = ['trip__route__route_code', 'stop__stop_name']
    ordering = ['-trip__trip_date', 'scheduled_arrival']
    
    fieldsets = (
        ('Thông tin', {
            'fields': ('trip', 'stop', 'location')
        }),
        ('Thời gian', {
            'fields': ('scheduled_arrival', 'actual_arrival', 'departure_time')
        }),
        ('Học sinh', {
            'fields': ('students_boarded', 'students_alighted')
        }),
        ('Ghi chú', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_trip(self, obj):
        return f"{obj.trip.route.route_code} - {obj.trip.trip_date}"
    get_trip.short_description = 'Chuyến đi'
    
    def get_stop(self, obj):
        return obj.stop.stop_name
    get_stop.short_description = 'Điểm dừng'
    
    def get_delay(self, obj):
        delay = obj.delay_minutes
        if delay is not None:
            if abs(delay) <= 5:
                return format_html('<span style="color: green;">Đúng giờ</span>')
            elif delay > 0:
                return format_html('<span style="color: red;">+{:.0f} phút</span>', delay)
            else:
                return format_html('<span style="color: blue;">{:.0f} phút</span>', delay)
        return '-'
    get_delay.short_description = 'Chênh lệch'
    
    def get_students(self, obj):
        boarded = obj.students_boarded
        alighted = obj.students_alighted
        return f"↑{boarded} ↓{alighted}"
    get_students.short_description = 'Học sinh'

@admin.register(TripIssue)
class TripIssueAdmin(admin.ModelAdmin):
    list_display = ['get_trip', 'get_issue_type', 'get_severity', 'get_status', 'reported_by', 'created_at']
    list_filter = ['issue_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['trip__route__route_code', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin sự cố', {
            'fields': ('trip', 'issue_type', 'severity', 'description', 'location', 'photo')
        }),
        ('Người báo cáo', {
            'fields': ('reported_by',)
        }),
        ('Xử lý', {
            'fields': ('is_resolved', 'resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_trip(self, obj):
        return f"{obj.trip.route.route_code} - {obj.trip.trip_date}"
    get_trip.short_description = 'Chuyến đi'
    
    def get_issue_type(self, obj):
        return obj.get_issue_type_display()
    get_issue_type.short_description = 'Loại sự cố'
    
    def get_severity(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.severity, '#000'),
            obj.get_severity_display()
        )
    get_severity.short_description = 'Mức độ'
    
    def get_status(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: green;">✓ Đã xử lý</span>')
        return format_html('<span style="color: red;">✗ Chưa xử lý</span>')
    get_status.short_description = 'Trạng thái'