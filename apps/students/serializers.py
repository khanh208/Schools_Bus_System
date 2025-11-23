from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Class, Area, Student, StudentNote, StudentDocument, EmergencyContact


class ClassSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'grade_level', 'room_number', 'teacher_name',
            'academic_year', 'is_active', 'student_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AreaSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Area
        fields = [
            'id', 'name', 'description', 'boundary', 
            'student_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = [
            'id', 'student', 'name', 'relationship', 'phone', 
            'email', 'address', 'is_primary'
        ]
        read_only_fields = ['id']


class StudentNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = StudentNote
        fields = [
            'id', 'student', 'note_type', 'title', 'content',
            'is_important', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class StudentDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    
    class Meta:
        model = StudentDocument
        fields = [
            'id', 'student', 'document_type', 'title', 'file',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class StudentListSerializer(serializers.ModelSerializer):
    """Serializer nhẹ để list danh sách học sinh (Đã bổ sung ID)"""
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    parent_name = serializers.CharField(source='parent.user.full_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_code', 'full_name', 'date_of_birth', 'age',
            'gender', 'class_name', 'area_name', 'parent_name',
            'photo', 'is_active',
            # --- QUAN TRỌNG: Bổ sung các trường ID này để form Edit hiển thị đúng ---
            'class_obj', 'area', 'parent' 
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    """Serializer chi tiết cho học sinh"""
    class_info = ClassSerializer(source='class_obj', read_only=True)
    area_info = AreaSerializer(source='area', read_only=True)
    parent_name = serializers.CharField(source='parent.user.full_name', read_only=True)
    parent_phone = serializers.CharField(source='parent.user.phone', read_only=True)
    
    age = serializers.IntegerField(read_only=True)
    current_route = serializers.SerializerMethodField()
    
    pickup_coordinates = serializers.SerializerMethodField()
    dropoff_coordinates = serializers.SerializerMethodField()
    
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    notes = StudentNoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_code', 'full_name', 'date_of_birth', 'age',
            'gender', 'class_obj', 'class_info', 'area', 'area_info',
            'parent', 'parent_name', 'parent_phone',
            'address', 'pickup_location', 'dropoff_location',
            'pickup_coordinates', 'dropoff_coordinates',
            'photo', 'special_needs', 'medical_conditions', 'blood_type',
            'is_active', 'current_route', 'emergency_contacts', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'student_code', 'created_at', 'updated_at']
    
    def get_current_route(self, obj):
        route = obj.current_route
        if route:
            return {
                'id': route.id,
                'route_code': route.route_code,
                'route_name': route.route_name
            }
        return None
    
    def get_pickup_coordinates(self, obj):
        return obj.get_pickup_coordinates()
    
    def get_dropoff_coordinates(self, obj):
        return obj.get_dropoff_coordinates()


class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer để tạo/cập nhật học sinh"""
    pickup_lat = serializers.FloatField(write_only=True, required=False)
    pickup_lng = serializers.FloatField(write_only=True, required=False)
    dropoff_lat = serializers.FloatField(write_only=True, required=False)
    dropoff_lng = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Student
        fields = [
            'student_code', 'full_name', 'date_of_birth', 'gender',
            'class_obj', 'area', 'parent', 'address',
            'pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng',
            'photo', 'special_needs', 'medical_conditions', 'blood_type',
            'is_active'
        ]
    
    def validate_student_code(self, value):
        if not self.instance and Student.objects.filter(student_code=value).exists():
            raise serializers.ValidationError("Student code already exists.")
        return value
    
    def create(self, validated_data):
        # Xử lý tọa độ nếu có
        pickup_lat = validated_data.pop('pickup_lat', 10.762622)
        pickup_lng = validated_data.pop('pickup_lng', 106.660172)
        dropoff_lat = validated_data.pop('dropoff_lat', 10.762622)
        dropoff_lng = validated_data.pop('dropoff_lng', 106.660172)
        
        validated_data['pickup_location'] = Point(pickup_lng, pickup_lat)
        validated_data['dropoff_location'] = Point(dropoff_lng, dropoff_lat)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'pickup_lat' in validated_data and 'pickup_lng' in validated_data:
            pickup_lat = validated_data.pop('pickup_lat')
            pickup_lng = validated_data.pop('pickup_lng')
            instance.pickup_location = Point(pickup_lng, pickup_lat)
        
        if 'dropoff_lat' in validated_data and 'dropoff_lng' in validated_data:
            dropoff_lat = validated_data.pop('dropoff_lat')
            dropoff_lng = validated_data.pop('dropoff_lng')
            instance.dropoff_location = Point(dropoff_lng, dropoff_lat)
        
        return super().update(instance, validated_data)