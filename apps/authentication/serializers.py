from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Driver, Parent, UserSession


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 'role',
            'avatar', 'is_active', 'is_verified', 'created_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'last_login']


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver profile"""
    user = UserSerializer(read_only=True)
    vehicle_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Driver
        fields = [
            'id', 'user', 'license_number', 'license_expiry', 
            'vehicle', 'vehicle_info', 'experience_years', 'rating', 
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'rating', 'created_at']
    
    def get_vehicle_info(self, obj):
        if obj.vehicle:
            return {
                'id': obj.vehicle.id,
                'plate_number': obj.vehicle.plate_number,
                'vehicle_type': obj.vehicle.vehicle_type,
                'capacity': obj.vehicle.capacity
            }
        return None


class ParentSerializer(serializers.ModelSerializer):
    """Serializer for Parent profile"""
    user = UserSerializer(read_only=True)
    children_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Parent
        fields = [
            'id', 'user', 'address', 'emergency_contact', 
            'children_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    # Extra fields for Driver
    license_number = serializers.CharField(required=False, write_only=True)
    license_expiry = serializers.DateField(required=False, write_only=True)
    
    # Extra fields for Parent
    address = serializers.CharField(required=False, write_only=True)
    emergency_contact = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'full_name', 'phone', 'role', 
            'license_number', 'license_expiry',
            'address', 'emergency_contact'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        
        # Validate role-specific fields
        if attrs['role'] == 'driver':
            if not attrs.get('license_number'):
                raise serializers.ValidationError({
                    "license_number": "License number is required for drivers."
                })
            if not attrs.get('license_expiry'):
                raise serializers.ValidationError({
                    "license_expiry": "License expiry date is required for drivers."
                })
        
        if attrs['role'] == 'parent':
            if not attrs.get('address'):
                raise serializers.ValidationError({
                    "address": "Address is required for parents."
                })
        
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm
        validated_data.pop('password_confirm')
        
        # Extract role-specific data
        license_number = validated_data.pop('license_number', None)
        license_expiry = validated_data.pop('license_expiry', None)
        address = validated_data.pop('address', None)
        emergency_contact = validated_data.pop('emergency_contact', None)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update role-specific profile
        if user.role == 'driver' and hasattr(user, 'driver_profile'):
            driver = user.driver_profile
            if license_number:
                driver.license_number = license_number
            if license_expiry:
                driver.license_expiry = license_expiry
            driver.save()
        
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            parent = user.parent_profile
            if address:
                parent.address = address
            if emergency_contact:
                parent.emergency_contact = emergency_contact
            parent.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                'Must include "username" and "password".',
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs


class TokenSerializer(serializers.Serializer):
    """Serializer for JWT tokens"""
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class ProfileSerializer(serializers.Serializer):
    """Unified profile serializer - FIXED"""
    # Trả về thông tin user ở level gốc
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    # Profile data (Driver/Parent)
    profile = serializers.SerializerMethodField()
    
    def get_profile(self, obj):
        if obj.role == 'driver' and hasattr(obj, 'driver_profile'):
            return DriverSerializer(obj.driver_profile).data
        elif obj.role == 'parent' and hasattr(obj, 'parent_profile'):
            return ParentSerializer(obj.parent_profile).data
        return None


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    # Driver fields
    license_number = serializers.CharField(required=False, allow_blank=True)
    license_expiry = serializers.DateField(required=False, allow_null=True)
    experience_years = serializers.IntegerField(required=False, allow_null=True)
    
    # Parent fields
    address = serializers.CharField(required=False, allow_blank=True)
    emergency_contact = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'full_name', 'phone', 'avatar',
            'license_number', 'license_expiry', 'experience_years',
            'address', 'emergency_contact'
        ]
    
    def update(self, instance, validated_data):
        # Update user fields
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.phone = validated_data.get('phone', instance.phone)
        
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
        
        instance.save()
        
        # Update driver profile
        if instance.role == 'driver' and hasattr(instance, 'driver_profile'):
            driver = instance.driver_profile
            driver.license_number = validated_data.get('license_number', driver.license_number)
            driver.license_expiry = validated_data.get('license_expiry', driver.license_expiry)
            driver.experience_years = validated_data.get('experience_years', driver.experience_years)
            driver.save()
        
        # Update parent profile
        if instance.role == 'parent' and hasattr(instance, 'parent_profile'):
            parent = instance.parent_profile
            parent.address = validated_data.get('address', parent.address)
            parent.emergency_contact = validated_data.get('emergency_contact', parent.emergency_contact)
            parent.save()
        
        return instance


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'username', 'device_info', 'ip_address',
            'is_active', 'created_at', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']


class FCMTokenSerializer(serializers.Serializer):
    """Serializer for FCM token registration"""
    token = serializers.CharField(required=True)
    device_type = serializers.ChoiceField(
        choices=['android', 'ios', 'web'],
        required=True
    )
    device_name = serializers.CharField(required=False, allow_blank=True)