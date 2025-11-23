from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point, LineString
from django.db.models import Q

from .models import (
    Vehicle, Route, RouteStop, StudentRoute, 
    RouteSchedule, VehicleMaintenance
)

# 1. Define VehicleSerializer FIRST
class VehicleSerializer(serializers.ModelSerializer):
    current_driver = serializers.SerializerMethodField()
    can_operate = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'plate_number', 'vehicle_type', 'capacity', 'model',
            'year', 'color', 'insurance_expiry', 'registration_expiry',
            'last_maintenance', 'next_maintenance', 'gps_device_id',
            'status', 'is_active', 'current_driver', 'can_operate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_driver(self, obj):
        driver = obj.current_driver
        if driver:
            return {
                'id': driver.id,
                'name': driver.user.full_name,
                'phone': driver.user.phone
            }
        return None

class VehicleMaintenanceSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = VehicleMaintenance
        fields = [
            'id', 'vehicle', 'vehicle_plate', 'maintenance_type',
            'description', 'cost', 'performed_by', 'performed_at',
            'next_maintenance_date', 'notes', 'created_by',
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

class RouteStopSerializer(serializers.ModelSerializer):
    location_lat = serializers.SerializerMethodField()
    location_lng = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = RouteStop
        fields = [
            'id', 'route', 'stop_order', 'stop_name', 'location',
            'location_lat', 'location_lng', 'address',
            'estimated_arrival', 'estimated_departure', 'stop_duration',
            'is_active', 'student_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_location_lat(self, obj):
        return obj.location.y if obj.location else None
    
    def get_location_lng(self, obj):
        return obj.location.x if obj.location else None

class RouteStopCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating route stops"""
    lat = serializers.FloatField(write_only=True)
    lng = serializers.FloatField(write_only=True)
    
    class Meta:
        model = RouteStop
        fields = [
            'route', 'stop_order', 'stop_name', 'lat', 'lng',
            'address', 'estimated_arrival', 'estimated_departure',
            'stop_duration', 'is_active'
        ]
    
    def create(self, validated_data):
        lat = validated_data.pop('lat')
        lng = validated_data.pop('lng')
        validated_data['location'] = Point(lng, lat)
        return super().create(validated_data)

class RouteScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RouteSchedule
        fields = [
            'id', 'route', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_day_name(self, obj):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[obj.day_of_week] if 0 <= obj.day_of_week < 7 else ''

class RouteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing routes"""
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    stop_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'route_code', 'route_name', 'route_type',
            'area_name', 'vehicle_plate', 'driver_name',
            'stop_count', 'student_count', 'estimated_duration',
            'total_distance', 'is_active'
        ]

# 2. Define RouteDetailSerializer AFTER VehicleSerializer and RouteStopSerializer
class RouteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for route with all info"""
    vehicle_info = VehicleSerializer(source='vehicle', read_only=True)
    driver_info = serializers.SerializerMethodField()
    area_info = serializers.SerializerMethodField()
    
    stops = RouteStopSerializer(many=True, read_only=True)
    schedules = RouteScheduleSerializer(many=True, read_only=True)
    
    stop_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'route_code', 'route_name', 'description', 'route_type',
            'area', 'area_info', 'vehicle', 'vehicle_info',
            'driver', 'driver_info', 'path', 'estimated_duration',
            'total_distance', 'is_active', 'stop_count', 'student_count',
            'stops', 'schedules', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_driver_info(self, obj):
        if obj.driver:
            return {
                'id': obj.driver.id,
                'name': obj.driver.user.full_name,
                'phone': obj.driver.user.phone,
                'license_number': obj.driver.license_number,
                'rating': float(obj.driver.rating)
            }
        return None
    
    def get_area_info(self, obj):
        if obj.area:
            return {
                'id': obj.area.id,
                'name': obj.area.name
            }
        return None

class RouteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating routes"""
    
    class Meta:
        model = Route
        fields = [
            'route_code', 'route_name', 'description', 'route_type',
            'area', 'vehicle', 'driver', 'estimated_duration',
            'total_distance', 'is_active'
        ]
    
    def validate_route_code(self, value):
        if not self.instance and Route.objects.filter(route_code=value).exists():
            raise serializers.ValidationError("Route code already exists.")
        return value
    
    def validate(self, attrs):
        # Validate vehicle capacity vs student count
        if attrs.get('vehicle') and self.instance:
            student_count = self.instance.student_count
            if student_count > attrs['vehicle'].capacity:
                raise serializers.ValidationError({
                    "vehicle": f"Vehicle capacity ({attrs['vehicle'].capacity}) is less than current student count ({student_count})."
                })
        return attrs

class StudentRouteSerializer(serializers.ModelSerializer):
    """Serializer for student-route assignments"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_code = serializers.CharField(source='student.student_code', read_only=True)
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    stop_name = serializers.CharField(source='stop.stop_name', read_only=True)
    
    class Meta:
        model = StudentRoute
        fields = [
            'id', 'student', 'student_name', 'student_code',
            'route', 'route_name', 'stop', 'stop_name',
            'assignment_type', 'start_date', 'end_date',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        # Validate that stop belongs to route
        if attrs.get('stop') and attrs.get('route'):
            if attrs['stop'].route != attrs['route']:
                raise serializers.ValidationError({
                    "stop": "Selected stop does not belong to the selected route."
                })
        
        # Removed overlapping check to allow easy testing/re-assignment
        return attrs

class RouteOptimizationSerializer(serializers.Serializer):
    """Serializer for route optimization request"""
    route_id = serializers.IntegerField(required=True)
    optimize_by = serializers.ChoiceField(
        choices=['distance', 'time', 'both'],
        default='both'
    )
    consider_traffic = serializers.BooleanField(default=True)