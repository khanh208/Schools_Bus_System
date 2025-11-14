from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import (
    Trip, LocationLog, StopArrival, TripIssue, ETARecord
)


class TripListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing trips"""
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    route_code = serializers.CharField(source='route.route_code', read_only=True)
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'route', 'route_name', 'route_code', 'driver_name',
            'vehicle_plate', 'trip_date', 'trip_type', 'status',
            'scheduled_start_time', 'actual_start_time',
            'total_students', 'checked_in_students', 'attendance_rate'
        ]


class TripDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for trip with all info"""
    route_info = serializers.SerializerMethodField()
    driver_info = serializers.SerializerMethodField()
    vehicle_info = serializers.SerializerMethodField()
    
    duration = serializers.IntegerField(read_only=True)
    delay = serializers.FloatField(read_only=True)
    is_delayed = serializers.BooleanField(read_only=True)
    attendance_rate = serializers.FloatField(read_only=True)
    current_location = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'route', 'route_info', 'driver', 'driver_info',
            'vehicle', 'vehicle_info', 'trip_date', 'trip_type',
            'scheduled_start_time', 'actual_start_time',
            'scheduled_end_time', 'actual_end_time', 'status',
            'total_students', 'checked_in_students', 'checked_out_students',
            'absent_students', 'attendance_rate', 'duration', 'delay',
            'is_delayed', 'current_location', 'notes',
            'cancellation_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_route_info(self, obj):
        return {
            'id': obj.route.id,
            'code': obj.route.route_code,
            'name': obj.route.route_name,
            'type': obj.route.route_type
        }
    
    def get_driver_info(self, obj):
        return {
            'id': obj.driver.id,
            'name': obj.driver.user.full_name,
            'phone': obj.driver.user.phone
        }
    
    def get_vehicle_info(self, obj):
        return {
            'id': obj.vehicle.id,
            'plate_number': obj.vehicle.plate_number,
            'type': obj.vehicle.vehicle_type,
            'capacity': obj.vehicle.capacity
        }
    
    def get_current_location(self, obj):
        location = obj.current_location
        if location:
            return {
                'lat': location.y,
                'lng': location.x
            }
        return None


class TripCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating trips"""
    
    class Meta:
        model = Trip
        fields = [
            'route', 'driver', 'vehicle', 'trip_date', 'trip_type',
            'scheduled_start_time', 'scheduled_end_time', 'notes'
        ]
    
    def validate(self, attrs):
        # Validate driver is available
        driver = attrs.get('driver')
        trip_date = attrs.get('trip_date')
        
        if driver and trip_date:
            conflicting_trips = Trip.objects.filter(
                driver=driver,
                trip_date=trip_date,
                status__in=['scheduled', 'in_progress']
            )
            
            if self.instance:
                conflicting_trips = conflicting_trips.exclude(pk=self.instance.pk)
            
            if conflicting_trips.exists():
                raise serializers.ValidationError({
                    "driver": "Driver already has a trip scheduled for this date."
                })
        
        # Validate vehicle is available
        vehicle = attrs.get('vehicle')
        if vehicle and trip_date:
            conflicting_trips = Trip.objects.filter(
                vehicle=vehicle,
                trip_date=trip_date,
                status__in=['scheduled', 'in_progress']
            )
            
            if self.instance:
                conflicting_trips = conflicting_trips.exclude(pk=self.instance.pk)
            
            if conflicting_trips.exists():
                raise serializers.ValidationError({
                    "vehicle": "Vehicle already assigned to another trip for this date."
                })
        
        return attrs
    
    def create(self, validated_data):
        # Count students assigned to route
        route = validated_data['route']
        from apps.routes.models import StudentRoute
        
        student_count = StudentRoute.objects.filter(
            route=route,
            is_active=True
        ).count()
        
        validated_data['total_students'] = student_count
        
        return super().create(validated_data)


class LocationLogSerializer(serializers.ModelSerializer):
    """Serializer for GPS location logs"""
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    
    class Meta:
        model = LocationLog
        fields = [
            'id', 'trip', 'driver', 'location', 'lat', 'lng',
            'accuracy', 'speed', 'heading', 'altitude',
            'battery_level', 'is_online', 'timestamp'
        ]
        read_only_fields = ['id']
    
    def get_lat(self, obj):
        return obj.location.y if obj.location else None
    
    def get_lng(self, obj):
        return obj.location.x if obj.location else None


class LocationLogCreateSerializer(serializers.Serializer):
    """Serializer for creating location logs"""
    trip_id = serializers.IntegerField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    accuracy = serializers.FloatField(required=False)
    speed = serializers.FloatField(required=False)
    heading = serializers.FloatField(required=False)
    altitude = serializers.FloatField(required=False)
    battery_level = serializers.IntegerField(required=False)
    timestamp = serializers.DateTimeField(required=False)
    
    def create(self, validated_data):
        trip_id = validated_data.pop('trip_id')
        lat = validated_data.pop('lat')
        lng = validated_data.pop('lng')
        
        from apps.tracking.models import Trip
        trip = Trip.objects.get(id=trip_id)
        
        location_log = LocationLog.objects.create(
            trip=trip,
            driver=trip.driver,
            location=Point(lng, lat),
            timestamp=validated_data.get('timestamp', timezone.now()),
            **validated_data
        )
        
        return location_log


class StopArrivalSerializer(serializers.ModelSerializer):
    """Serializer for stop arrivals"""
    stop_name = serializers.CharField(source='stop.stop_name', read_only=True)
    delay_minutes = serializers.FloatField(read_only=True)
    is_on_time = serializers.BooleanField(read_only=True)
    dwell_time = serializers.FloatField(read_only=True)
    
    class Meta:
        model = StopArrival
        fields = [
            'id', 'trip', 'stop', 'stop_name', 'scheduled_arrival',
            'actual_arrival', 'departure_time', 'location',
            'students_boarded', 'students_alighted', 'delay_minutes',
            'is_on_time', 'dwell_time', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TripIssueSerializer(serializers.ModelSerializer):
    """Serializer for trip issues"""
    reported_by_name = serializers.CharField(source='reported_by.full_name', read_only=True)
    location_lat = serializers.SerializerMethodField()
    location_lng = serializers.SerializerMethodField()
    
    class Meta:
        model = TripIssue
        fields = [
            'id', 'trip', 'issue_type', 'severity', 'description',
            'location', 'location_lat', 'location_lng', 'reported_by',
            'reported_by_name', 'is_resolved', 'resolved_at',
            'resolution_notes', 'photo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reported_by', 'created_at', 'updated_at']
    
    def get_location_lat(self, obj):
        return obj.location.y if obj.location else None
    
    def get_location_lng(self, obj):
        return obj.location.x if obj.location else None


class ETARecordSerializer(serializers.ModelSerializer):
    """Serializer for ETA records"""
    stop_name = serializers.CharField(source='stop.stop_name', read_only=True)
    
    class Meta:
        model = ETARecord
        fields = [
            'id', 'trip', 'stop', 'stop_name', 'calculated_at',
            'estimated_arrival', 'actual_arrival', 'distance_remaining',
            'estimated_time_minutes', 'prediction_error_minutes'
        ]
        read_only_fields = ['id']


class TripTrackingSerializer(serializers.Serializer):
    """Serializer for real-time trip tracking data"""
    trip = TripDetailSerializer()
    current_location = serializers.DictField()
    next_stop = serializers.DictField()
    eta_minutes = serializers.IntegerField()
    distance_to_next_stop = serializers.FloatField()
    progress_percentage = serializers.FloatField()
    recent_locations = LocationLogSerializer(many=True)