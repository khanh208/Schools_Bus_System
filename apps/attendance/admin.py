from django.contrib import admin
from django.utils.html import format_html
from .models import Attendance, AttendanceException, AttendanceReport, AttendanceAlert

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_trip', 'get_attendance_type', 'get_status', 'check_time', 'checked_by']
    list_filter = ['attendance_type', 'status', 'check_time', 'trip__trip_date']
    search_fields = ['student__full_name', 'trip__route__route_code']
    ordering = ['-check_time']
    date_hierarchy = 'check_time'
    
    fieldsets = (
        ('Thông tin điểm danh', {
            'fields': ('trip', 'student', 'stop', 'attendance_type', 'status')
        }),
        ('Thời gian và vị trí', {
            'fields': ('check_time', 'location')
        }),
        ('Người điểm danh', {
            'fields': ('checked_by',)
        }),
        ('Thông tin bổ sung', {
            'fields': ('temperature', 'photo', 'notes'),
            'classes': ('collapse',)
        }),
        ('Thông báo', {
            'fields': ('parent_notified', 'notification_sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'parent_notified', 'notification_sent_at']
    
    def get_student(self, obj):
        return f"{obj.student.student_code} - {obj.student.full_name}"
    get_student.short_description = 'Học sinh'
    
    def get_trip(self, obj):
        return f"{obj.trip.route.route_code} - {obj.trip.trip_date}"
    get_trip.short_description = 'Chuyến đi'
    
    def get_attendance_type(self, obj):
        colors = {
            'check_in': '#007bff',
            'check_out': '#28a745',
            'absent': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            colors.get(obj.attendance_type, '#000'),
            obj.get_attendance_type_display()
        )
    get_attendance_type.short_description = 'Loại'
    
    def get_status(self, obj):
        colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'excused': 'blue'
        }
        icons = {
            'present': '✓',
            'absent': '✗',
            'late': '⏰',
            'excused': 'ℹ'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, 'black'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    get_status.short_description = 'Trạng thái'

@admin.register(AttendanceException)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_trip', 'get_attendance_type', 'get_status', 'check_time', 'checked_by']
    list_filter = ['attendance_type', 'status', 'check_time', 'trip__trip_date']
    search_fields = ['student__full_name', 'trip__route__route_code']
    ordering = ['-check_time']
    date_hierarchy = 'check_time'
    
    fieldsets = (
        ('Thông tin điểm danh', {
            'fields': ('trip', 'student', 'stop', 'attendance_type', 'status')
        }),
        ('Thời gian và vị trí', {
            'fields': ('check_time', 'location')
        }),
        ('Người điểm danh', {
            'fields': ('checked_by',)
        }),
        ('Thông tin bổ sung', {
            'fields': ('temperature', 'photo', 'notes'),
            'classes': ('collapse',)
        }),
        ('Thông báo', {
            'fields': ('parent_notified', 'notification_sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'parent_notified', 'notification_sent_at']
    
    def get_student(self, obj):
        return f"{obj.student.student_code} - {obj.student.full_name}"
    get_student.short_description = 'Học sinh'
    
    def get_trip(self, obj):
        return f"{obj.trip.route.route_code} - {obj.trip.trip_date}"
    get_trip.short_description = 'Chuyến đi'
    
    def get_attendance_type(self, obj):
        colors = {
            'check_in': '#007bff',
            'check_out': '#28a745',
            'absent': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            colors.get(obj.attendance_type, '#000'),
            obj.get_attendance_type_display()
        )
    get_attendance_type.short_description = 'Loại'
    
    def get_status(self, obj):
        colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'excused': 'blue'
        }
        icons = {
            'present': '✓',
            'absent': '✗',
            'late': '⏰',
            'excused': 'ℹ'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, 'black'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    get_status.short_description = 'Trạng thái'


@admin.register(AttendanceException)
class AttendanceExceptionAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_exception_type', 'start_date', 'end_date', 'is_active']
    list_filter = ['exception_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['student__student_code', 'student__full_name']
    ordering = ['-start_date']

    fieldsets = (
        ('Thông tin ngoại lệ', {
            'fields': ('student', 'exception_type', 'reason')
        }),
        ('Thời gian áp dụng', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Hệ thống', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'created_by']

    def get_student(self, obj):
        return f"{obj.student.student_code} - {obj.student.full_name}"
    get_student.short_description = 'Học sinh'

    def get_exception_type(self, obj):
        # Nếu exception_type là TextChoices, dùng get_exception_type_display()
        label = getattr(obj, 'get_exception_type_display', lambda: obj.exception_type)()
        return label
    get_exception_type.short_description = 'Loại ngoại lệ'