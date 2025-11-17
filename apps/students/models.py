from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Class(models.Model):
    name = models.CharField('Tên lớp', max_length=100)
    grade_level = models.IntegerField(
        'Khối',
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    room_number = models.CharField('Phòng học', max_length=20, blank=True, null=True)
    teacher_name = models.CharField('Giáo viên chủ nhiệm', max_length=255, blank=True, null=True)
    academic_year = models.CharField('Năm học', max_length=20)
    is_active = models.BooleanField('Đang hoạt động', default=True)
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    
    class Meta:
        db_table = 'classes'
        verbose_name = 'Lớp học'
        verbose_name_plural = 'Lớp học'
        ordering = ['grade_level', 'name']
        unique_together = [['name', 'academic_year']]
    
    def __str__(self):
        return f"Lớp {self.name} - Khối {self.grade_level} ({self.academic_year})"
    
    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()


class Area(models.Model):
    name = models.CharField('Tên khu vực', max_length=255)
    description = models.TextField('Mô tả', blank=True, null=True)
    boundary = models.PolygonField('Ranh giới', srid=4326, blank=True, null=True)
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    
    class Meta:
        db_table = 'areas'
        verbose_name = 'Khu vực'
        verbose_name_plural = 'Khu vực'
        ordering = ['name']
    
    def __str__(self):
        return self.name    
    
    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()
    
    def is_point_in_area(self, point):
        """Check if a point is within this area's boundary"""
        if self.boundary and isinstance(point, Point):
            return self.boundary.contains(point)
        return False


class GenderChoices(models.TextChoices):
    MALE = 'male', 'Nam'
    FEMALE = 'female', 'Nữ'
    OTHER = 'other', 'Khác'


class Student(models.Model):
    student_code = models.CharField('Mã học sinh', max_length=50, unique=True, db_index=True)
    full_name = models.CharField('Họ và tên', max_length=255)
    date_of_birth = models.DateField('Ngày sinh')
    gender = models.CharField('Giới tính', max_length=10, choices=GenderChoices.choices)
    
    # Relationships
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='students',
        verbose_name='Lớp học'
    )
    area = models.ForeignKey(
        Area, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='students',
        verbose_name='Khu vực'
    )
    parent = models.ForeignKey(
        'authentication.Parent', 
        on_delete=models.CASCADE, 
        related_name='students',
        verbose_name='Phụ huynh'
    )
    
    # Address & Location
    address = models.TextField('Địa chỉ')
    pickup_location = models.PointField('Vị trí đón', srid=4326)
    dropoff_location = models.PointField('Vị trí trả', srid=4326)
    
    # Additional Info
    photo = models.ImageField('Ảnh', upload_to='students/', blank=True, null=True)
    special_needs = models.TextField('Nhu cầu đặc biệt', blank=True, null=True)
    medical_conditions = models.TextField('Tình trạng sức khỏe', blank=True, null=True)
    blood_type = models.CharField('Nhóm máu', max_length=5, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField('Đang hoạt động', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Học sinh'
        verbose_name_plural = 'Học sinh'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.student_code} - {self.full_name}"
    
    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def has_special_needs(self):
        return bool(self.special_needs)
    
    @property
    def current_route(self):
        """Get current active route assignment"""
        from apps.routes.models import StudentRoute
        assignment = StudentRoute.objects.filter(
            student=self,
            is_active=True,
            start_date__lte=timezone.now().date()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now().date())
        ).first()
        return assignment.route if assignment else None
    
    def get_pickup_coordinates(self):
        """Return pickup location as [lng, lat]"""
        return [self.pickup_location.x, self.pickup_location.y]
    
    def get_dropoff_coordinates(self):
        """Return dropoff location as [lng, lat]"""
        return [self.dropoff_location.x, self.dropoff_location.y]


class StudentNote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notes')
    created_by = models.ForeignKey('authentication.User', on_delete=models.CASCADE)

    note_type = models.CharField(
        max_length=50,
        help_text="Loại ghi chú (sức khỏe, hành vi, chung)"
    )  # medical, behavioral, general

    title = models.CharField(
        max_length=255,
        verbose_name="Tiêu đề ghi chú"
    )
    content = models.TextField(
        verbose_name="Nội dung ghi chú"
    )
    is_important = models.BooleanField(
        default=False,
        verbose_name="Quan trọng?"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = 'student_notes'
        ordering = ['-created_at']
        verbose_name = "Ghi chú học sinh"
        verbose_name_plural = "Ghi chú học sinh"

    def __str__(self):
        return f"Ghi chú của {self.student.full_name} - {self.title}"


class StudentDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')

    document_type = models.CharField(
        max_length=50,
        help_text="Loại tài liệu (giấy khai sinh, hồ sơ sức khỏe, …)"
    )  # birth_certificate, medical, etc

    title = models.CharField(
        max_length=255,
        verbose_name="Tên tài liệu"
    )
    file = models.FileField(
        upload_to='student_documents/',
        verbose_name="Tập tin"
    )

    uploaded_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        verbose_name="Người tải lên"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tải lên"
    )

    class Meta:
        db_table = 'student_documents'
        ordering = ['-uploaded_at']
        verbose_name = "Tài liệu học sinh"
        verbose_name_plural = "Tài liệu học sinh"

    def __str__(self):
        return f"Tài liệu của {self.student.full_name} - {self.title}"



class EmergencyContact(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='emergency_contacts', verbose_name='Học sinh')
    name = models.CharField('Họ tên', max_length=255)
    relationship = models.CharField('Quan hệ', max_length=100)
    phone = models.CharField('Số điện thoại', max_length=20)
    email = models.EmailField('Email', blank=True, null=True)
    address = models.TextField('Địa chỉ', blank=True, null=True)
    is_primary = models.BooleanField('Liên hệ chính', default=False)
    
    class Meta:
        db_table = 'emergency_contacts'
        verbose_name = 'Liên hệ khẩn cấp'
        verbose_name_plural = 'Liên hệ khẩn cấp'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.student.full_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary contact per student
        if self.is_primary:
            EmergencyContact.objects.filter(
                student=self.student, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)