from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Driver, Parent

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'get_role_display', 'get_status', 'created_at']
    list_filter = ['role', 'is_active', 'is_verified', 'created_at']
    search_fields = ['username', 'email', 'full_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin đăng nhập', {
            'fields': ('username', 'password')
        }),
        ('Thông tin cá nhân', {
            'fields': ('full_name', 'email', 'phone', 'avatar')
        }),
        ('Phân quyền', {
            'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser')
        }),
        ('Thông tin quan trọng', {
            'fields': ('last_login', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Tạo người dùng mới', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'full_name', 'role'),
        }),
    )
    
    readonly_fields = ['created_at', 'last_login']
    
    def get_role_display(self, obj):
        colors = {
            'admin': '#dc3545',
            'driver': '#28a745',
            'parent': '#007bff'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.role, '#000'),
            obj.get_role_display()
        )
    get_role_display.short_description = 'Vai trò'
    
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Hoạt động</span>')
        return format_html('<span style="color: red;">✗ Ngừng</span>')
    get_status.short_description = 'Trạng thái'

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['get_driver_name', 'license_number', 'get_status_display', 'rating', 'experience_years', 'get_vehicle']
    list_filter = ['status', 'created_at']
    search_fields = ['user__full_name', 'license_number', 'user__phone']
    
    fieldsets = (
        ('Thông tin tài xế', {
            'fields': ('user', 'license_number', 'license_expiry', 'experience_years')
        }),
        ('Phân công', {
            'fields': ('vehicle', 'status', 'rating')
        }),
    )
    
    def get_driver_name(self, obj):
        return obj.user.full_name
    get_driver_name.short_description = 'Họ tên'
    
    def get_status_display(self, obj):
        colors = {
            'available': 'green',
            'on_trip': 'orange',
            'off_duty': 'gray'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    get_status_display.short_description = 'Trạng thái'
    
    def get_vehicle(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.plate_number} ({obj.vehicle.vehicle_type})"
        return "Chưa có xe"
    get_vehicle.short_description = 'Xe được gán'

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['get_parent_name', 'get_email', 'get_phone', 'get_children_count']
    search_fields = ['user__full_name', 'user__email', 'user__phone']
    
    fieldsets = (
        ('Thông tin phụ huynh', {
            'fields': ('user', 'address', 'emergency_contact')
        }),
    )
    
    def get_parent_name(self, obj):
        return obj.user.full_name
    get_parent_name.short_description = 'Họ tên'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Số điện thoại'
    
    def get_children_count(self, obj):
        count = obj.students.filter(is_active=True).count()
        return format_html('<span style="color: blue; font-weight: bold;">{} học sinh</span>', count)
    get_children_count.short_description = 'Số con'

# Thay đổi tiêu đề admin site
admin.site.site_header = "🚌 Hệ thống quản lý xe đưa đón học sinh"
admin.site.site_title = "Quản lý xe bus"
admin.site.index_title = "Bảng điều khiển"