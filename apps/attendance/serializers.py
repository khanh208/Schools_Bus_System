# apps/attendance/serializers.py
from rest_framework import serializers
from django.utils import timezone

from .models import Attendance  # ✅ Quan trọng: import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer cho bản ghi điểm danh"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_code = serializers.CharField(source='student.student_code', read_only=True)
    student_photo = serializers.ImageField(source='student.photo', read_only=True)
    stop_name = serializers.CharField(source='stop.stop_name', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id',
            'trip',
            'student',
            'student_name',
            'student_code',
            'student_photo',
            'stop',
            'stop_name',
            'attendance_type',
            'status',
            'check_time',
            'location',
            'checked_by',
            'checked_by_name',
            'notes',
            'temperature',
            'parent_notified',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'parent_notified',
            'created_at',
        ]


class AttendanceCheckInSerializer(serializers.ModelSerializer):
    """Serializer cho việc điểm danh (check-in)"""
    lat = serializers.FloatField(write_only=True, required=False)
    lng = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Attendance
        fields = [
            'trip',
            'student',
            'stop',
            'attendance_type',
            'status',
            'lat',
            'lng',
            'notes',
            'temperature',
        ]

    def validate(self, attrs):
        # Đảm bảo học sinh thuộc tuyến của trip
        trip = attrs.get('trip')
        student = attrs.get('student')

        if trip and student:
            from apps.routes.models import StudentRoute

            assignment = StudentRoute.objects.filter(
                student=student,
                route=trip.route,
                is_active=True
            ).first()

            if not assignment:
                raise serializers.ValidationError({
                    "student": "Student is not assigned to this route."
                })

        # Kiểm tra trùng điểm danh
        if Attendance.objects.filter(
            trip=trip,
            student=student,
            attendance_type=attrs.get('attendance_type')
        ).exists():
            raise serializers.ValidationError({
                "student": "Attendance already recorded for this student."
            })

        return attrs

    def create(self, validated_data):
        lat = validated_data.pop('lat', None)
        lng = validated_data.pop('lng', None)

        if lat is not None and lng is not None:
            from django.contrib.gis.geos import Point
            validated_data['location'] = Point(lng, lat)

        validated_data['check_time'] = timezone.now()
        validated_data['checked_by'] = self.context['request'].user

        attendance = super().create(validated_data)

        # Gửi thông báo cho phụ huynh
        attendance.send_notification_to_parent()

        # Cập nhật thống kê trip
        trip = attendance.trip
        if attendance.attendance_type == 'check_in':
            if attendance.status == 'present':
                trip.checked_in_students += 1
            elif attendance.status == 'absent':
                trip.absent_students += 1
        elif attendance.attendance_type == 'check_out':
            trip.checked_out_students += 1
        trip.save()

        return attendance


class BulkAttendanceSerializer(serializers.Serializer):
    """Serializer cho điểm danh hàng loạt"""
    trip_id = serializers.IntegerField()
    attendance_records = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_attendance_records(self, value):
        required_fields = ['student_id', 'status']
        for record in value:
            for field in required_fields:
                if field not in record:
                    raise serializers.ValidationError(
                        f"Missing required field: {field}"
                    )
        return value
