from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, Route, RouteStop, StudentRoute, RouteSchedule, VehicleMaintenance

class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ['stop_order', 'stop_name', 'address', 'estimated_arrival', 'estimated_departure', 'is_active']
    ordering = ['stop_order']
    verbose_name = 'Điểm dừng'
    verbose_name_plural = 'Danh sách điểm dừng'
    
    # Thêm CSS cho inline
    class Media:
        css = {
            'all': ['admin/css/custom_inline.css']
        }

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
    autocomplete_fields = ['student', 'stop']
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
    
    # Thêm inlines
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
    
    # Autocomplete
    autocomplete_fields = ['vehicle', 'driver', 'area']
    
    # Read only
    readonly_fields = ['created_at', 'updated_at']
    
    # Định nghĩa lại các methods get_... như trước
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