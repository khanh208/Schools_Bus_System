from rest_framework import serializers
from django.contrib.gis.geos import Point
from django.utils import timezone

from .models import Trip, LocationLog, StopArrival


class TripListSerializer(serializers.ModelSerializer):
    """
    Serializer nhẹ để list danh sách chuyến đi
    """
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    route_code = serializers.CharField(source='route.route_code', read_only=True)
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)
    attendance_rate = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'route', 'route_name', 'route_code',
            'driver_name', 'vehicle_plate',
            'trip_date', 'trip_type', 'status',
            'scheduled_start_time', 'actual_start_time',
            'total_students', 'checked_in_students',
            'attendance_rate',
        ]

    def get_attendance_rate(self, obj):
        # SỬA LỖI: Kiểm tra kỹ để tránh chia cho 0
        if obj.total_students and obj.total_students > 0:
            try:
                rate = (obj.checked_in_students / obj.total_students) * 100.0
                return round(rate, 1)
            except ZeroDivisionError:
                return 0.0
        return 0.0


class TripDetailSerializer(serializers.ModelSerializer):
    """
    Chi tiết 1 chuyến đi để driver / admin / parent xem
    """
    route_info = serializers.SerializerMethodField()
    driver_info = serializers.SerializerMethodField()
    vehicle_info = serializers.SerializerMethodField()

    duration = serializers.SerializerMethodField()
    delay = serializers.SerializerMethodField()
    is_delayed = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    current_location = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'route', 'route_info',
            'driver', 'driver_info',
            'vehicle', 'vehicle_info',
            'trip_date', 'trip_type',
            'scheduled_start_time', 'actual_start_time',
            'scheduled_end_time', 'actual_end_time',
            'status',
            'total_students',
            'checked_in_students',
            'checked_out_students',
            'notes',
            'duration', 'delay', 'is_delayed',
            'attendance_rate',
            'current_location',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_route_info(self, obj):
        return {
            'id': obj.route.id,
            'code': obj.route.route_code,
            'name': obj.route.route_name,
            'type': getattr(obj.route, 'route_type', None),
        }

    def get_driver_info(self, obj):
        return {
            'id': obj.driver.id,
            'name': obj.driver.user.full_name,
            'phone': obj.driver.user.phone,
        }

    def get_vehicle_info(self, obj):
        return {
            'id': obj.vehicle.id,
            'plate_number': obj.vehicle.plate_number,
            'type': obj.vehicle.vehicle_type,
            'capacity': getattr(obj.vehicle, 'capacity', None),
        }

    def get_duration(self, obj):
        if hasattr(obj, 'duration') and obj.duration is not None:
            return obj.duration
        if obj.actual_start_time and obj.actual_end_time:
            return (obj.actual_end_time - obj.actual_start_time).total_seconds() / 60
        return None

    def get_delay(self, obj):
        if hasattr(obj, 'delay') and obj.delay is not None:
            return obj.delay
        if obj.actual_start_time and obj.scheduled_start_time:
            return (obj.actual_start_time - obj.scheduled_start_time).total_seconds() / 60
        return None

    def get_is_delayed(self, obj):
        delay = self.get_delay(obj)
        if delay is None:
            return False
        return delay > 5

    def get_attendance_rate(self, obj):
        # SỬA LỖI: Tương tự như trên
        if obj.total_students and obj.total_students > 0:
            try:
                rate = (obj.checked_in_students / obj.total_students) * 100.0
                return round(rate, 1)
            except ZeroDivisionError:
                return 0.0
        return 0.0

    def get_current_location(self, obj):
        latest_log = obj.location_logs.order_by('-timestamp').first()
        if not latest_log or not latest_log.location:
            return None
        return {
            'lat': latest_log.location.y,
            'lng': latest_log.location.x,
            'speed': float(latest_log.speed) if latest_log.speed else 0.0,
            'timestamp': latest_log.timestamp,
        }


class TripCreateSerializer(serializers.ModelSerializer):
    """
    Tạo / cập nhật chuyến đi
    """
    class Meta:
        model = Trip
        fields = [
            'route', 'driver', 'vehicle',
            'trip_date', 'trip_type',
            'scheduled_start_time', 'scheduled_end_time',
            'notes',
        ]

    def validate(self, attrs):
        driver = attrs.get('driver')
        trip_date = attrs.get('trip_date')
        vehicle = attrs.get('vehicle')

        if driver and trip_date:
            qs = Trip.objects.filter(
                driver=driver,
                trip_date=trip_date,
                status__in=['scheduled', 'in_progress'],
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'driver': 'Tài xế đã có chuyến trong ngày này.',
                })

        if vehicle and trip_date:
            qs = Trip.objects.filter(
                vehicle=vehicle,
                trip_date=trip_date,
                status__in=['scheduled', 'in_progress'],
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'vehicle': 'Xe đã được gán cho chuyến khác trong ngày này.',
                })

        return attrs

    def create(self, validated_data):
        route = validated_data['route']
        from apps.routes.models import StudentRoute

        student_count = StudentRoute.objects.filter(
            route=route,
            is_active=True,
        ).count()

        validated_data['total_students'] = student_count
        return super().create(validated_data)


class LocationLogSerializer(serializers.ModelSerializer):
    """
    Log vị trí GPS
    """
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    class Meta:
        model = LocationLog
        fields = [
            'id',
            'trip', 'driver',
            'location', 'lat', 'lng',
            'speed',
            'timestamp',
        ]
        read_only_fields = ['id']

    def get_lat(self, obj):
        return obj.location.y if obj.location else None

    def get_lng(self, obj):
        return obj.location.x if obj.location else None


class LocationLogCreateSerializer(serializers.Serializer):
    """
    Input đơn giản cho mobile driver gửi vị trí
    """
    trip_id = serializers.IntegerField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    speed = serializers.FloatField(required=False)
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
            speed=validated_data.get('speed'),
        )
        return location_log


class StopArrivalSerializer(serializers.ModelSerializer):
    """
    Thời điểm xe đến từng điểm dừng
    """
    stop_name = serializers.CharField(source='stop.stop_name', read_only=True)
    delay_minutes = serializers.SerializerMethodField()

    class Meta:
        model = StopArrival
        fields = [
            'id',
            'trip', 'stop', 'stop_name',
            'scheduled_arrival', 'actual_arrival',
            'students_boarded', 'students_alighted',
            'delay_minutes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_delay_minutes(self, obj):
        if hasattr(obj, 'delay_minutes'):
            return obj.delay_minutes
        if obj.actual_arrival and obj.scheduled_arrival:
            return (obj.actual_arrival - obj.scheduled_arrival).total_seconds() / 60.0
        return None


class TripTrackingSerializer(serializers.Serializer):
    """
    Gói dữ liệu tổng hợp cho màn hình real-time tracking
    """
    trip = TripDetailSerializer()
    current_location = serializers.DictField(allow_null=True)
    next_stop = serializers.DictField(allow_null=True)
    eta_minutes = serializers.IntegerField(allow_null=True)
    distance_to_next_stop = serializers.FloatField(allow_null=True)
    progress_percentage = serializers.FloatField()
    recent_locations = LocationLogSerializer(many=True)