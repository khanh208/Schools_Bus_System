class BackupLog(models.Model):
    """Log of backup operations"""
    backup_type = models.CharField(
        max_length=50,
        choices=[
            ('full', 'Full Backup'),
            ('incremental', 'Incremental Backup'),
            ('manual', 'Manual Backup'),
            ('scheduled', 'Scheduled Backup'),
        ]
    )
    
    # Files
    backup_path = models.CharField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
    )
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Details
    tables_backed_up = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # User
    performed_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backups'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'backup_logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.backup_type} - {self.started_at} ({self.status})"
    
    def calculate_duration(self):
        """Calculate backup duration"""
        if self.completed_at and self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
            self.save(update_fields=['duration_seconds'])


class RestoreLog(models.Model):
    """Log of restore operations"""
    backup_log = models.ForeignKey(
        BackupLog, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restores'
    )
    
    restore_point = models.DateTimeField(
        help_text="The point in time being restored to"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('rolled_back', 'Rolled Back'),
        ]
    )
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Details
    tables_restored = models.JSONField(default=list, blank=True)
    records_restored = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    # User
    performed_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        related_name='restores'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'restore_logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Restore to {self.restore_point} - {self.status}"


class AuditLog(models.Model):
    """Audit trail for system actions"""
    user = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    action = models.CharField(
        max_length=50,
        choices=[
            ('create', 'Create'),
            ('update', 'Update'),
            ('delete', 'Delete'),
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('backup', 'Backup'),
            ('restore', 'Restore'),
            ('export', 'Export'),
        ]
    )
    
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField(null=True, blank=True)
    
    # Changes
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'System'
        return f"{username} - {self.action} {self.entity_type}"


class SystemSetting(models.Model):
    """System-wide settings"""
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    setting_type = models.CharField(
        max_length=50,
        choices=[
            ('string', 'String'),
            ('number', 'Number'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ]
    )
    description = models.TextField(blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'authentication.User', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'system_settings'
        ordering = ['setting_key']
    
    def __str__(self):
        return f"{self.setting_key} = {self.setting_value}"
    
    def get_value(self):
        """Parse and return the setting value based on type"""
        import json
        
        if self.setting_type == 'boolean':
            return self.setting_value.lower() in ['true', '1', 'yes']
        elif self.setting_type == 'number':
            try:
                return float(self.setting_value)
            except ValueError:
                return 0
        elif self.setting_type == 'json':
            try:
                return json.loads(self.setting_value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.setting_value