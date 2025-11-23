# apps/backup/models.py
from django.db import models

class BackupLog(models.Model):
    """Log sao lưu dữ liệu"""
    backup_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Thủ công'),
            ('auto', 'Tự động'),
            ('full', 'Toàn bộ'),
            ('incremental', 'Tăng phần')
        ]
    )
    
    backup_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Thành công'),
            ('failed', 'Thất bại'),
            ('in_progress', 'Đang xử lý'),
        ],
        default='in_progress'
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    tables_backed_up = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    performed_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'backup_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backup {self.id} - {self.created_at}"


class RestoreLog(models.Model):
    """Log phục hồi dữ liệu"""
    backup_log = models.ForeignKey(BackupLog, on_delete=models.CASCADE, related_name='restores')
    restore_point = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Đang chờ'),
            ('in_progress', 'Đang xử lý'),
            ('success', 'Thành công'),
            ('failed', 'Thất bại'),
        ],
        default='pending'
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    tables_restored = models.JSONField(default=list, blank=True)
    records_restored = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    performed_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restore_logs'
        ordering = ['-created_at']


class AuditLog(models.Model):
    """Log kiểm toán hệ thống (Ghi lại các tác động quan trọng)"""
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, LOGIN...
    entity_type = models.CharField(max_length=100)  # Tên bảng/Model
    entity_id = models.CharField(max_length=100, null=True, blank=True)
    
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']


class SystemSetting(models.Model):
    """Cấu hình hệ thống động"""
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    setting_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    description = models.TextField(blank=True, null=True)
    
    updated_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
    
    def __str__(self):
        return self.setting_key

    def get_value(self):
        if self.setting_type == 'integer':
            try:
                return int(self.setting_value)
            except:
                return 0
        if self.setting_type == 'boolean':
            return self.setting_value.lower() == 'true'
        return self.setting_value