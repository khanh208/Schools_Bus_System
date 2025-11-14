from rest_framework import serializers
from django.utils import timezone
from .models import (
    Attendance, AttendanceException, AttendanceReport, AttendanceAlert
)


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for attendance records"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_code = serializers.CharField(source='student.student_code', read_only=True)
    student_photo = serializers.ImageField(source='student.photo', read_only=True)
    stop_name = serializers.CharField(source='stop.stop_name', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.full_name', read_only=True)
    is_on_time = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'trip', 'student', 'student_name', 'student_code',
            'student_photo', 'stop', 'stop_name', 'attendance_type',
            'status', 'check_time', 'location', 'checked_by',
            'checked_by_name', 'photo', 'notes', 'temperature',
            'parent_notified', 'notification_sent_at', 'is_on_time',
            'created_at'
        ]
        read_only_fields = ['id', 'parent_notified', 'notification_sent_at', 'created_at']


class AttendanceCheckInSerializer(serializers.ModelSerializer):
    """Serializer for checking in students"""
    lat = serializers.FloatField(write_only=True, required=False)
    lng = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Attendance
        fields = [
            'trip', 'student', 'stop', 'attendance_type',
            'status', 'lat', 'lng', 'photo', 'notes', 'temperature'
        ]
    
    def validate(self, attrs):
        # Ensure student is assigned to this trip's route
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
        
        # Check for duplicate attendance
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
        
        if lat and lng:
            from django.contrib.gis.geos import Point
            validated_data['location'] = Point(lng, lat)
        
        validated_data['check_time'] = timezone.now()
        validated_data['checked_by'] = self.context['request'].user
        
        attendance = super().create(validated_data)
        
        # Send notification to parent
        attendance.send_notification_to_parent()
        
        # Update trip statistics
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
    """Serializer for bulk attendance operations"""
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


class AttendanceExceptionSerializer(serializers.ModelSerializer):
    """Serializer for attendance exceptions"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = AttendanceException
        fields = [
            'id', 'student', 'student_name', 'exception_type',
            'start_date', 'end_date', 'reason', 'approved_by',
            'approved_by_name', 'supporting_document', 'is_approved',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class AttendanceReportSerializer(serializers.ModelSerializer):
    """Serializer for attendance reports"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    
    class Meta:
        model = AttendanceReport
        fields = [
            'id', 'student', 'student_name', 'report_type',
            'start_date', 'end_date', 'total_days', 'present_days',
            'absent_days', 'late_days', 'excused_days', 'attendance_rate',
            'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class AttendanceAlertSerializer(serializers.ModelSerializer):
    """Serializer for attendance alerts"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.full_name', read_only=True)
    
    class Meta:
        model = AttendanceAlert
        fields = [
            'id', 'student', 'student_name', 'alert_type', 'severity',
            'description', 'is_resolved', 'resolved_at', 'resolved_by',
            'resolved_by_name', 'resolution_notes', 'parent_notified',
            'admin_notified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AttendanceStatsSerializer(serializers.Serializer):
    """Serializer for attendance statistics"""
    date = serializers.DateField()
    total_students = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    excused = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
