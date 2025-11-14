from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Class(models.Model):
    name = models.CharField(max_length=100)
    grade_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    room_number = models.CharField(max_length=20, blank=True, null=True)
    teacher_name = models.CharField(max_length=255, blank=True, null=True)
    academic_year = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'classes'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['grade_level', 'name']
        unique_together = [['name', 'academic_year']]
    
    def __str__(self):
        return f"{self.name} - Grade {self.grade_level} ({self.academic_year})"
    
    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()


class Area(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    boundary = models.PolygonField(srid=4326, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'areas'
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'
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
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'


class Student(models.Model):
    student_code = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GenderChoices.choices)
    
    # Relationships
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='students'
    )
    area = models.ForeignKey(
        Area, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='students'
    )
    parent = models.ForeignKey(
        'authentication.Parent', 
        on_delete=models.CASCADE, 
        related_name='students'
    )
    
    # Address & Location
    address = models.TextField()
    pickup_location = models.PointField(srid=4326)
    dropoff_location = models.PointField(srid=4326)
    
    # Additional Info
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    special_needs = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    blood_type = models.CharField(max_length=5, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['student_code']),
            models.Index(fields=['full_name']),
            models.Index(fields=['is_active']),
        ]
    
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
    note_type = models.CharField(max_length=50)  # medical, behavioral, general
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.student.full_name} - {self.title}"


class StudentDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50)  # birth_certificate, medical, etc
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='student_documents/')
    uploaded_by = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'student_documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.title}"


class EmergencyContact(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'emergency_contacts'
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