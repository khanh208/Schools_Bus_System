from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, Route, RouteStop, StudentRoute, RouteSchedule, VehicleMaintenance

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'vehicle_type', 'capacity', 'get_status_display', 'get_driver', 'get_insurance_status']
    list_filter = ['status', 'vehicle_type', 'is_active']
    search_fields = ['plate_number', 'model']
    ordering = ['plate_number']
    
    fieldsets = (
        ('Thông tin xe', {
            'fields': ('plate_number', 'vehicle_type', 'model', 'year', 'color', 'capacity')
        }),
        ('Thiết bị GPS', {
            'fields': ('gps_device_id',)
        }),
        ('Giấy tờ', {
            'fields': ('insurance_expiry', 'registration_expiry')
        }),
        ('Bảo dưỡng', {
            'fields': ('last_maintenance', 'next_maintenance'),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('status', 'is_active')
        }),
    )
    
    def get_status_display(self, obj):
        colors = {
            'active': 'green',
            'maintenance': 'orange',
            'inactive': 'gray'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    get_status_display.short_description = 'Trạng thái'
    
    def get_driver(self, obj):
        driver = obj.current_driver
        if driver:
            return format_html('<span style="color: blue;">{}</span>', driver.user.full_name)
        return format_html('<span style="color: gray;">Chưa có tài xế</span>')
    get_driver.short_description = 'Tài xế'
    
    def get_insurance_status(self, obj):
        if obj.is_insurance_valid:
            return format_html('<span style="color: green;">✓ Còn hạn</span>')
        return format_html('<span style="color: red;">✗ Hết hạn</span>')
    get_insurance_status.short_description = 'Bảo hiểm'
    
    # Inline cho Maintenance
    class MaintenanceInline(admin.TabularInline):
        model = VehicleMaintenance
        extra = 0
        fields = ['maintenance_type', 'performed_at', 'cost', 'next_maintenance_date']
        readonly_fields = ['performed_at']
        verbose_name = 'Lịch sử bảo dưỡng'
        verbose_name_plural = 'Lịch sử bảo dưỡng'
        ordering = ['-performed_at']
    
    inlines = [MaintenanceInline]

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_code', 'route_name', 'get_route_type', 'get_vehicle', 'get_driver', 'get_stop_count', 'get_status']
    list_filter = ['route_type', 'is_active', 'area']
    search_fields = ['route_code', 'route_name']
    ordering = ['route_code']
    
    fieldsets = (
        ('Thông tin tuyến', {
            'fields': ('route_code', 'route_name', 'description', 'route_type', 'area')
        }),
        ('Phân công', {
            'fields': ('vehicle', 'driver')
        }),
        ('Thông số', {
            'fields': ('estimated_duration', 'total_distance', 'path'),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    def get_route_type(self, obj):
        colors = {
            'pickup': '#007bff',
            'dropoff': '#28a745',
            'both': '#ffc107'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.route_type, '#000'),
            obj.get_route_type_display()
        )
    get_route_type.short_description = 'Loại tuyến'
    
    def get_vehicle(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.plate_number}"
        return format_html('<span style="color: red;">Chưa có xe</span>')
    get_vehicle.short_description = 'Xe'
    
    def get_driver(self, obj):
        if obj.driver:
            return obj.driver.user.full_name
        return format_html('<span style="color: red;">Chưa có tài xế</span>')
    get_driver.short_description = 'Tài xế'
    
    def get_stop_count(self, obj):
        count = obj.stop_count
        return format_html('<span style="color: blue; font-weight: bold;">{} điểm</span>', count)
    get_stop_count.short_description = 'Số điểm dừng'
    
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Hoạt động</span>')
        return format_html('<span style="color: red;">✗ Ngừng</span>')
    get_status.short_description = 'Trạng thái'
    
    # Inline cho Route Stops
    class RouteStopInline(admin.TabularInline):
        model = RouteStop
        extra = 1
        fields = ['stop_order', 'stop_name', 'estimated_arrival', 'estimated_departure', 'is_active']
        ordering = ['stop_order']
        verbose_name = 'Điểm dừng'
        verbose_name_plural = 'Danh sách điểm dừng'
    
    inlines = [RouteStopInline]

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['get_route', 'stop_order', 'stop_name', 'estimated_arrival', 'get_student_count', 'get_status']
    list_filter = ['route', 'is_active']
    search_fields = ['stop_name', 'address', 'route__route_code']
    ordering = ['route', 'stop_order']
    
    fieldsets = (
        ('Thông tin điểm dừng', {
            'fields': ('route', 'stop_order', 'stop_name', 'address', 'location')
        }),
        ('Thời gian', {
            'fields': ('estimated_arrival', 'estimated_departure', 'stop_duration')
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    def get_route(self, obj):
        return f"{obj.route.route_code} - {obj.route.route_name}"
    get_route.short_description = 'Tuyến đường'
    
    def get_student_count(self, obj):
        count = obj.student_count
        return format_html('<span style="color: blue;">{} học sinh</span>', count)
    get_student_count.short_description = 'Số học sinh'
    
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    get_status.short_description = 'Hoạt động'

@admin.register(StudentRoute)
class StudentRouteAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_route', 'get_stop', 'get_assignment_type', 'start_date', 'end_date', 'get_status']
    list_filter = ['assignment_type', 'is_active', 'route']
    search_fields = ['student__full_name', 'route__route_code']
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Phân công học sinh', {
            'fields': ('student', 'route', 'stop', 'assignment_type')
        }),
        ('Thời gian', {
            'fields': ('start_date', 'end_date')
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    def get_student(self, obj):
        return f"{obj.student.student_code} - {obj.student.full_name}"
    get_student.short_description = 'Học sinh'
    
    def get_route(self, obj):
        return obj.route.route_code
    get_route.short_description = 'Tuyến'
    
    def get_stop(self, obj):
        return obj.stop.stop_name
    get_stop.short_description = 'Điểm dừng'
    
    def get_assignment_type(self, obj):
        colors = {
            'pickup': '#007bff',
            'dropoff': '#28a745',
            'both': '#ffc107'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.assignment_type, '#000'),
            obj.get_assignment_type_display()
        )
    get_assignment_type.short_description = 'Loại'
    
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Đang hoạt động</span>')
        return format_html('<span style="color: gray;">✗ Đã kết thúc</span>')
    get_status.short_description = 'Trạng thái'

@admin.register(RouteSchedule)
class RouteScheduleAdmin(admin.ModelAdmin):
    list_display = ['get_route', 'get_day_name', 'start_time', 'end_time', 'get_status']
    list_filter = ['day_of_week', 'is_active', 'route']
    search_fields = ['route__route_code', 'route__route_name']
    ordering = ['route', 'day_of_week', 'start_time']
    
    fieldsets = (
        ('Lịch trình', {
            'fields': ('route', 'day_of_week', 'start_time', 'end_time')
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    def get_route(self, obj):
        return f"{obj.route.route_code} - {obj.route.route_name}"
    get_route.short_description = 'Tuyến đường'
    
    def get_day_name(self, obj):
        days = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        if 0 <= obj.day_of_week < 7:
            return format_html('<span style="font-weight: bold;">{}</span>', days[obj.day_of_week])
        return obj.day_of_week
    get_day_name.short_description = 'Thứ'
    
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    get_status.short_description = 'Hoạt động'

@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['get_vehicle', 'maintenance_type', 'performed_at', 'cost', 'next_maintenance_date', 'created_by']
    list_filter = ['maintenance_type', 'performed_at']
    search_fields = ['vehicle__plate_number', 'maintenance_type', 'description']
    ordering = ['-performed_at']
    date_hierarchy = 'performed_at'
    
    fieldsets = (
        ('Thông tin bảo dưỡng', {
            'fields': ('vehicle', 'maintenance_type', 'description', 'performed_at', 'performed_by')
        }),
        ('Chi phí', {
            'fields': ('cost',)
        }),
        ('Lịch bảo dưỡng tiếp theo', {
            'fields': ('next_maintenance_date',)
        }),
        ('Ghi chú', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_by', 'created_at']
    
    def get_vehicle(self, obj):
        return obj.vehicle.plate_number
    get_vehicle.short_description = 'Xe'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)