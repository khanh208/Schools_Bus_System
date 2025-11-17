from django.contrib import admin
from django.utils.html import format_html
from .models import Class, Area, Student, EmergencyContact, StudentNote, StudentDocument

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade_level', 'academic_year', 'teacher_name', 'room_number', 'get_student_count', 'get_status']
    list_filter = ['grade_level', 'academic_year', 'is_active']
    search_fields = ['name', 'teacher_name', 'room_number']
    ordering = ['grade_level', 'name']
    
    fieldsets = (
        ('Thông tin lớp học', {
            'fields': ('name', 'grade_level', 'room_number', 'academic_year')
        }),
        ('Giáo viên', {
            'fields': ('teacher_name',)
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    def get_student_count(self, obj):
        count = obj.students.filter(is_active=True).count()
        return format_html('<span style="color: blue; font-weight: bold;">{} học sinh</span>', count)
    get_student_count.short_description = 'Sĩ số'
    
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Đang học</span>')
        return format_html('<span style="color: red;">✗ Đã kết thúc</span>')
    get_status.short_description = 'Trạng thái'

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_student_count']
    search_fields = ['name', 'description']
    
    def get_student_count(self, obj):
        count = obj.students.filter(is_active=True).count()
        return format_html('<span style="color: blue;">{} học sinh</span>', count)
    get_student_count.short_description = 'Số học sinh'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_code', 'full_name', 'get_class', 'get_parent', 'get_age', 'get_status']
    list_filter = ['class_obj', 'area', 'gender', 'is_active']
    search_fields = ['student_code', 'full_name', 'parent__user__full_name']
    ordering = ['student_code']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('student_code', 'full_name', 'date_of_birth', 'gender', 'photo')
        }),
        ('Phân công', {
            'fields': ('class_obj', 'area', 'parent')
        }),
        ('Địa chỉ và vị trí', {
            'fields': ('address', 'pickup_location', 'dropoff_location')
        }),
        ('Thông tin sức khỏe', {
            'fields': ('blood_type', 'special_needs', 'medical_conditions'),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_class(self, obj):
        if obj.class_obj:
            return f"Lớp {obj.class_obj.name}"
        return "Chưa có lớp"
    get_class.short_description = 'Lớp học'
    
    def get_parent(self, obj):
        return obj.parent.user.full_name
    get_parent.short_description = 'Phụ huynh'
    
    def get_age(self, obj):
        age = obj.age
        return f"{age} tuổi"
    get_age.short_description = 'Tuổi'
    def get_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Đang học</span>')
        return format_html('<span style="color: red;">✗ Đã nghỉ</span>')
    get_status.short_description = 'Trạng thái'
    
    # Inline cho Emergency Contacts
    class EmergencyContactInline(admin.TabularInline):
        model = EmergencyContact
        extra = 1
        fields = ['name', 'relationship', 'phone', 'is_primary']
        verbose_name = 'Liên hệ khẩn cấp'
        verbose_name_plural = 'Danh sách liên hệ khẩn cấp'
    
    inlines = [EmergencyContactInline]

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['get_student_name', 'name', 'relationship', 'phone', 'get_primary']
    list_filter = ['is_primary', 'relationship']
    search_fields = ['student__full_name', 'name', 'phone']
    
    def get_student_name(self, obj):
        return obj.student.full_name
    get_student_name.short_description = 'Học sinh'
    
    def get_primary(self, obj):
        if obj.is_primary:
            return format_html('<span style="color: red; font-weight: bold;">★ Chính</span>')
        return ''
    get_primary.short_description = 'Ưu tiên'

@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'title', 'note_type', 'get_important', 'created_by', 'created_at']
    list_filter = ['note_type', 'is_important', 'created_at']
    search_fields = ['student__full_name', 'title', 'content']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin ghi chú', {
            'fields': ('student', 'note_type', 'title', 'content', 'is_important')
        }),
        ('Người tạo', {
            'fields': ('created_by',)
        }),
    )
    
    readonly_fields = ['created_by', 'created_at']
    
    def get_student(self, obj):
        return obj.student.full_name
    get_student.short_description = 'Học sinh'
    
    def get_important(self, obj):
        if obj.is_important:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Quan trọng</span>')
        return ''
    get_important.short_description = 'Mức độ'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nếu tạo mới
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'document_type', 'title', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['student__full_name', 'title']
    ordering = ['-uploaded_at']
    
    def get_student(self, obj):
        return obj.student.full_name
    get_student.short_description = 'Học sinh'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)