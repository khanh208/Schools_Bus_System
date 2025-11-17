from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    DRIVER = 'driver', 'Driver'
    PARENT = 'parent', 'Parent'


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        if not username:
            raise ValueError('Username is required')
        
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
    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # ⚠️ QUAN TRỌNG: Thêm dòng này
    password = models.CharField(max_length=128)  # Django expects 'password', not 'password_hash'
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # FCM token for push notifications
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.username})"
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_driver(self):
        return self.role == UserRole.DRIVER
    
    @property
    def is_parent(self):
        return self.role == UserRole.PARENT
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.username


class DriverStatus(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    ON_TRIP = 'on_trip', 'On Trip'
    OFF_DUTY = 'off_duty', 'Off Duty'


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField()
    vehicle = models.ForeignKey('routes.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')
    experience_years = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    status = models.CharField(max_length=20, choices=DriverStatus.choices, default=DriverStatus.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'drivers'
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'
    
    def __str__(self):
        return f"Driver: {self.user.full_name}"
    
    @property
    def is_license_valid(self):
        return self.license_expiry > timezone.now().date()
    
    def can_drive(self):
        return self.is_license_valid and self.status == DriverStatus.AVAILABLE


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    address = models.TextField()
    emergency_contact = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'parents'
        verbose_name = 'Parent'
        verbose_name_plural = 'Parents'
    
    def __str__(self):
        return f"Parent: {self.user.full_name}"
    
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