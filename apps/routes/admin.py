from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, Route, RouteStop, StudentRoute, RouteSchedule, VehicleMaintenance

# Register Vehicle first
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'vehicle_type', 'capacity', 'get_status', 'insurance_expiry']
    list_filter = ['status', 'vehicle_type']
    search_fields = ['plate_number', 'model', 'gps_device_id']
    ordering = ['plate_number']
    
    fieldsets = (
        ('Thông tin xe', {
            'fields': ('plate_number', 'vehicle_type', 'capacity', 'model', 'year', 'color')
        }),
        ('Giấy tờ', {
            'fields': ('insurance_expiry', 'registration_expiry', 'last_maintenance', 'next_maintenance')
        }),
        ('GPS', {
            'fields': ('gps_device_id',)
        }),
        ('Trạng thái', {
            'fields': ('status', 'is_active')
        }),
    )
    
    def get_status(self, obj):
        colors = {
            'active': 'green',
            'maintenance': 'orange',
            'inactive': 'red'
        }
        return format_html(
            '<span style="color: {};">●</span> {}',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    get_status.short_description = 'Trạng thái'

# Register RouteStop
@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'stop_order', 'stop_name', 'estimated_arrival', 'is_active']
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

class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ['stop_order', 'stop_name', 'address', 'estimated_arrival', 'estimated_departure', 'is_active']
    ordering = ['stop_order']
    verbose_name = 'Điểm dừng'
    verbose_name_plural = 'Danh sách điểm dừng'

class RouteScheduleInline(admin.TabularInline):
    model = RouteSchedule
    extra = 1
    fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
    verbose_name = 'Lịch trình'
    verbose_name_plural = 'Lịch trình hoạt động'

class StudentRouteInline(admin.TabularInline):
    model = StudentRoute
    extra = 0
    fields = ['student', 'stop', 'assignment_type', 'start_date', 'end_date', 'is_active']
    raw_id_fields = ['student', 'stop']
    verbose_name = 'Học sinh'
    verbose_name_plural = 'Danh sách học sinh trên tuyến'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'stop')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_code', 'route_name', 'get_route_type', 'get_vehicle', 'get_driver', 'get_stop_count', 'get_status']
    list_filter = ['route_type', 'is_active', 'area']
    search_fields = ['route_code', 'route_name']
    ordering = ['route_code']
    
    inlines = [RouteStopInline, RouteScheduleInline, StudentRouteInline]
    
    fieldsets = (
        ('📋 Thông tin tuyến', {
            'fields': ('route_code', 'route_name', 'description', 'route_type', 'area')
        }),
        ('🚗 Phân công', {
            'fields': ('vehicle', 'driver'),
            'description': 'Chọn xe và tài xế cho tuyến này'
        }),
        ('📊 Thông số', {
            'fields': ('estimated_duration', 'total_distance'),
            'classes': ('collapse',)
        }),
        ('✅ Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    raw_id_fields = ['vehicle', 'driver', 'area']
    readonly_fields = ['created_at', 'updated_at']
    
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

@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'maintenance_type', 'performed_at', 'cost', 'next_maintenance_date']
    list_filter = ['maintenance_type', 'performed_at']
    search_fields = ['vehicle__plate_number', 'maintenance_type', 'description']
    ordering = ['-performed_at']
    
    fieldsets = (
        ('Thông tin bảo trì', {
            'fields': ('vehicle', 'maintenance_type', 'description', 'cost')
        }),
        ('Thực hiện', {
            'fields': ('performed_by', 'performed_at', 'next_maintenance_date')
        }),
        ('Ghi chú', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(RouteSchedule)
class RouteScheduleAdmin(admin.ModelAdmin):
    list_display = ['route', 'get_day_name', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['route__route_code', 'route__route_name']
    ordering = ['route', 'day_of_week', 'start_time']
    
    def get_day_name(self, obj):
        days = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        return days[obj.day_of_week] if 0 <= obj.day_of_week < 7 else ''
    get_day_name.short_description = 'Ngày'

@admin.register(StudentRoute)
class StudentRouteAdmin(admin.ModelAdmin):
    list_display = ['student', 'route', 'stop', 'assignment_type', 'start_date', 'is_active']
    list_filter = ['assignment_type', 'is_active', 'route']
    search_fields = ['student__full_name', 'student__student_code', 'route__route_code']
    ordering = ['-created_at']
    raw_id_fields = ['student', 'route', 'stop']
    
    fieldsets = (
        ('Phân công', {
            'fields': ('student', 'route', 'stop', 'assignment_type')
        }),
        ('Thời gian', {
            'fields': ('start_date', 'end_date')
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )