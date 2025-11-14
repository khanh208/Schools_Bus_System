from rest_framework import serializers
from .models import (
    DailyReport, TripPerformance, DriverPerformanceReport,
    RoutePerformanceReport, SystemStatistics
)
from apps.backup.models import BackupLog, RestoreLog, AuditLog, SystemSetting


class DailyReportSerializer(serializers.ModelSerializer):
    """Serializer for daily reports"""
    
    class Meta:
        model = DailyReport
        fields = [
            'id', 'report_date', 'total_trips', 'completed_trips',
            'cancelled_trips', 'in_progress_trips',
            'total_students_transported', 'total_present',
            'total_absent', 'total_late', 'on_time_percentage',
            'late_percentage', 'average_delay_minutes',
            'total_distance_km', 'total_duration_minutes',
            'total_issues', 'critical_issues', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class TripPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for trip performance"""
    trip_info = serializers.SerializerMethodField()
    
    class Meta:
        model = TripPerformance
        fields = [
            'id', 'trip', 'trip_info', 'scheduled_duration',
            'actual_duration', 'delay_minutes', 'is_on_time',
            'attendance_rate', 'distance_km', 'average_speed',
            'stops_completed', 'stops_total', 'issues_reported',
            'driver_rating', 'parent_feedback_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_trip_info(self, obj):
        return {
            'id': obj.trip.id,
            'route_code': obj.trip.route.route_code,
            'date': obj.trip.trip_date,
            'type': obj.trip.trip_type
        }


class DriverPerformanceReportSerializer(serializers.ModelSerializer):
    """Serializer for driver performance reports"""
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    
    class Meta:
        model = DriverPerformanceReport
        fields = [
            'id', 'driver', 'driver_name', 'report_type',
            'start_date', 'end_date', 'total_trips', 'completed_trips',
            'cancelled_trips', 'on_time_trips', 'delayed_trips',
            'on_time_percentage', 'average_delay_minutes',
            'total_distance_km', 'average_rating', 'total_ratings',
            'total_issues', 'critical_issues', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class RoutePerformanceReportSerializer(serializers.ModelSerializer):
    """Serializer for route performance reports"""
    route_code = serializers.CharField(source='route.route_code', read_only=True)
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    
    class Meta:
        model = RoutePerformanceReport
        fields = [
            'id', 'route', 'route_code', 'route_name', 'report_type',
            'start_date', 'end_date', 'total_trips', 'completed_trips',
            'average_duration', 'on_time_percentage',
            'average_delay_minutes', 'average_students_per_trip',
            'average_attendance_rate', 'average_distance_km',
            'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class SystemStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for system statistics"""
    
    class Meta:
        model = SystemStatistics
        fields = [
            'id', 'date', 'total_users', 'active_parents',
            'active_drivers', 'total_students', 'active_students',
            'total_vehicles', 'active_vehicles', 'total_routes',
            'active_routes', 'overall_on_time_percentage',
            'overall_attendance_rate', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class ReportGenerateSerializer(serializers.Serializer):
    """Serializer for generating reports"""
    report_type = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly', 'custom']
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    entity_type = serializers.ChoiceField(
        choices=['driver', 'route', 'student', 'system'],
        required=False
    )
    entity_id = serializers.IntegerField(required=False)
    
    def validate(self, attrs):
        report_type = attrs.get('report_type')
        
        if report_type == 'custom':
            if not attrs.get('start_date') or not attrs.get('end_date'):
                raise serializers.ValidationError({
                    "date_range": "Start date and end date are required for custom reports."
                })
        
        if attrs.get('entity_type') in ['driver', 'route', 'student']:
            if not attrs.get('entity_id'):
                raise serializers.ValidationError({
                    "entity_id": f"Entity ID is required for {attrs['entity_type']} reports."
                })
        
        return attrs


class ExportReportSerializer(serializers.Serializer):
    """Serializer for exporting reports"""
    report_type = serializers.ChoiceField(
        choices=['daily', 'driver', 'route', 'attendance']
    )
    format = serializers.ChoiceField(
        choices=['pdf', 'excel', 'csv'],
        default='pdf'
    )
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    include_charts = serializers.BooleanField(default=True)


# ============================================
# apps/backup/serializers.py
# ============================================


class BackupLogSerializer(serializers.ModelSerializer):
    """Serializer for backup logs"""
    performed_by_name = serializers.CharField(
        source='performed_by.full_name', 
        read_only=True
    )
    
    class Meta:
        model = BackupLog
        fields = [
            'id', 'backup_type', 'backup_path', 'file_name',
            'file_size_mb', 'status', 'started_at', 'completed_at',
            'duration_seconds', 'tables_backed_up', 'error_message',
            'performed_by', 'performed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreateBackupSerializer(serializers.Serializer):
    """Serializer for creating backups"""
    backup_type = serializers.ChoiceField(
        choices=['full', 'incremental', 'manual']
    )
    description = serializers.CharField(required=False, allow_blank=True)


class RestoreLogSerializer(serializers.ModelSerializer):
    """Serializer for restore logs"""
    performed_by_name = serializers.CharField(
        source='performed_by.full_name',
        read_only=True
    )
    backup_file = serializers.CharField(
        source='backup_log.file_name',
        read_only=True
    )
    
    class Meta:
        model = RestoreLog
        fields = [
            'id', 'backup_log', 'backup_file', 'restore_point',
            'status', 'started_at', 'completed_at', 'duration_seconds',
            'tables_restored', 'records_restored', 'error_message',
            'performed_by', 'performed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RestoreBackupSerializer(serializers.Serializer):
    """Serializer for restoring backups"""
    backup_id = serializers.IntegerField()
    confirm = serializers.BooleanField(default=False)
    
    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must confirm the restore operation."
            )
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action', 'entity_type',
            'entity_id', 'old_value', 'new_value', 'ip_address',
            'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SystemSettingSerializer(serializers.ModelSerializer):
    """Serializer for system settings"""
    updated_by_name = serializers.CharField(
        source='updated_by.full_name',
        read_only=True
    )
    parsed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemSetting
        fields = [
            'id', 'setting_key', 'setting_value', 'setting_type',
            'description', 'parsed_value', 'updated_at',
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'updated_at', 'updated_by']
    
    def get_parsed_value(self, obj):
        return obj.get_value()


class UpdateSystemSettingSerializer(serializers.Serializer):
    """Serializer for updating system settings"""
    setting_key = serializers.CharField()
    setting_value = serializers.CharField()
    
    def validate_setting_key(self, value):
        if not SystemSetting.objects.filter(setting_key=value).exists():
            raise serializers.ValidationError(
                f"Setting '{value}' does not exist."
            )
        return value


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    today_stats = serializers.DictField()
    active_trips = serializers.IntegerField()
    total_students = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    on_time_percentage = serializers.FloatField()
    active_drivers = serializers.IntegerField()
    active_vehicles = serializers.IntegerField()
    pending_issues = serializers.IntegerField()
    recent_alerts = serializers.ListField()


class AnalyticsSerializer(serializers.Serializer):
    """Serializer for analytics data"""
    period = serializers.ChoiceField(
        choices=['week', 'month', 'quarter', 'year']
    )
    metrics = serializers.ListField(
        child=serializers.DictField()
    )
    trends = serializers.DictField()
    comparisons = serializers.DictField()


class StudentAttendanceTrendSerializer(serializers.Serializer):
    """Serializer for student attendance trends"""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    period = serializers.CharField()
    attendance_data = serializers.ListField(
        child=serializers.DictField()
    )
    average_rate = serializers.FloatField()
    trend = serializers.CharField()  # improving, declining, stable


class RouteEfficiencySerializer(serializers.Serializer):
    """Serializer for route efficiency analysis"""
    route_id = serializers.IntegerField()
    route_code = serializers.CharField()
    average_duration = serializers.FloatField()
    average_delay = serializers.FloatField()
    on_time_rate = serializers.FloatField()
    fuel_efficiency = serializers.FloatField()
    student_utilization = serializers.FloatField()
    recommendations = serializers.ListField(
        child=serializers.CharField()
    )


class DriverPerformanceTrendSerializer(serializers.Serializer):
    """Serializer for driver performance trends"""
    driver_id = serializers.IntegerField()
    driver_name = serializers.CharField()
    period = serializers.CharField()
    performance_data = serializers.ListField(
        child=serializers.DictField()
    )
    average_rating = serializers.FloatField()
    on_time_rate = serializers.FloatField()
    incident_count = serializers.IntegerField()
    trend = serializers.CharField()


class ComparisonReportSerializer(serializers.Serializer):
    """Serializer for comparison reports"""
    entity_type = serializers.ChoiceField(
        choices=['routes', 'drivers', 'periods']
    )
    entity_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    metric = serializers.ChoiceField(
        choices=[
            'on_time_rate', 'attendance_rate', 'efficiency',
            'distance', 'duration', 'issues'
        ]
    )
    period = serializers.CharField()
    data = serializers.ListField(
        child=serializers.DictField()
    )