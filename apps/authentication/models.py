from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Quản trị viên'
    DRIVER = 'driver', 'Tài xế'
    PARENT = 'parent', 'Phụ huynh'


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Địa chỉ email là bắt buộc')
        if not username:
            raise ValueError('Tên đăng nhập là bắt buộc')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField('Tên đăng nhập', max_length=150, unique=True, db_index=True)
    email = models.EmailField('Email', max_length=255, unique=True, db_index=True)
    full_name = models.CharField('Họ và tên', max_length=255)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Số điện thoại phải có định dạng: '+999999999'. Tối đa 15 chữ số."
    )
    phone = models.CharField('Số điện thoại', validators=[phone_regex], max_length=20, blank=True, null=True)
    role = models.CharField('Vai trò', max_length=20, choices=UserRole.choices)
    avatar = models.ImageField('Ảnh đại diện', upload_to='avatars/', blank=True, null=True)
    password = models.CharField('Mật khẩu', max_length=128)
    
    # Status fields
    is_active = models.BooleanField('Đang hoạt động', default=True)
    is_verified = models.BooleanField('Đã xác thực', default=False)
    is_staff = models.BooleanField('Là nhân viên', default=False)
    
    # Timestamps
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    last_login = models.DateTimeField('Đăng nhập lần cuối', null=True, blank=True)
    
    # FCM token for push notifications
    fcm_token = models.CharField('FCM Token', max_length=255, blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.username})"


class DriverStatus(models.TextChoices):
    AVAILABLE = 'available', 'Sẵn sàng'
    ON_TRIP = 'on_trip', 'Đang chạy'
    OFF_DUTY = 'off_duty', 'Nghỉ việc'


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile', verbose_name='Người dùng')
    license_number = models.CharField('Số giấy phép lái xe', max_length=50, unique=True)
    license_expiry = models.DateField('Ngày hết hạn GPLX')
    vehicle = models.ForeignKey('routes.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers', verbose_name='Xe được gán')
    experience_years = models.IntegerField('Số năm kinh nghiệm', default=0)
    rating = models.DecimalField('Đánh giá', max_digits=3, decimal_places=2, default=5.00)
    status = models.CharField('Trạng thái', max_length=20, choices=DriverStatus.choices, default=DriverStatus.AVAILABLE)
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    
    class Meta:
        db_table = 'drivers'
        verbose_name = 'Tài xế'
        verbose_name_plural = 'Tài xế'
    
    def __str__(self):
        return f"Tài xế: {self.user.full_name}"


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile', verbose_name='Người dùng')
    address = models.TextField('Địa chỉ')
    emergency_contact = models.CharField('Liên hệ khẩn cấp', max_length=20)
    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    
    class Meta:
        db_table = 'parents'
        verbose_name = 'Phụ huynh'
        verbose_name_plural = 'Phụ huynh'
    
    def __str__(self):
        return f"Phụ huynh: {self.user.full_name}"
    
    @property
    def children_count(self):
        return self.students.filter(is_active=True).count()


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Session for {self.user.username} - {self.ip_address}"


# Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create Driver or Parent profile based on role"""
    if created:
        if instance.role == UserRole.DRIVER:
            Driver.objects.create(
                user=instance,
                license_number=f"TEMP_{instance.id}",
                license_expiry=timezone.now().date() + timezone.timedelta(days=365)
            )
        elif instance.role == UserRole.PARENT:
            Parent.objects.create(user=instance, address="", emergency_contact="")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save related profile when user is saved"""
    if instance.role == UserRole.DRIVER and hasattr(instance, 'driver_profile'):
        instance.driver_profile.save()
    elif instance.role == UserRole.PARENT and hasattr(instance, 'parent_profile'):
        instance.parent_profile.save()