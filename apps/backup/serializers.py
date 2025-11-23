# apps/backup/serializers.py
from rest_framework import serializers
from .models import BackupLog, RestoreLog, AuditLog, SystemSetting


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