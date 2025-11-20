# apps/backup/models.py - ĐƠN GIẢN
from django.db import models

class BackupLog(models.Model):
    """Log sao lưu dữ liệu"""
    backup_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Thủ công'),
            ('auto', 'Tự động'),
        ]
    )
    
    backup_path = models.CharField(max_length=500)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Thành công'),
            ('failed', 'Thất bại'),
        ]
    )
    
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
        return f"Backup - {self.created_at}"
