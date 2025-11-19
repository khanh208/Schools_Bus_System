# apps/notifications/tasks.py
"""
Celery tasks for background processing
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_daily_summary():
    """Send daily summary to admins"""
    from apps.reports.models import DailyReport
    from apps.authentication.models import User
    from .services import NotificationService
    
    today = timezone.now().date()
    
    try:
        report = DailyReport.objects.get(report_date=today)
    except DailyReport.DoesNotExist:
        logger.warning(f"No daily report for {today}")
        return
    
    admins = User.objects.filter(role='admin', is_active=True)
    
    context = {
        'report': report,
        'date': today
    }
    
    for admin in admins:
        NotificationService.send_from_template(
            template_code='DAILY_SUMMARY',
            user=admin,
            context=context,
            channels=['email', 'in_app']
        )
    
    logger.info(f"Sent daily summary to {admins.count()} admins")


@shared_task
def generate_daily_reports():
    """Generate daily reports"""
    from apps.reports.models import DailyReport
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    try:
        report = DailyReport.generate_report(yesterday)
        logger.info(f"Generated daily report for {yesterday}")
        return f"Report generated: {report.id}"
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return f"Error: {str(e)}"


@shared_task
def check_vehicle_maintenance():
    """Check vehicles needing maintenance"""
    from apps.routes.models import Vehicle
    from apps.authentication.models import User
    from .services import NotificationService
    
    # Get vehicles needing maintenance
    vehicles = Vehicle.objects.filter(
        is_active=True,
        next_maintenance__lte=timezone.now().date() + timedelta(days=7)
    )
    
    if not vehicles.exists():
        return "No vehicles need maintenance"
    
    admins = User.objects.filter(role='admin', is_active=True)
    
    for admin in admins:
        context = {
            'vehicles': vehicles,
            'count': vehicles.count()
        }
        
        NotificationService.send_from_template(
            template_code='MAINTENANCE_REMINDER',
            user=admin,
            context=context,
            channels=['email', 'in_app']
        )
    
    logger.info(f"Sent maintenance reminders for {vehicles.count()} vehicles")
    return f"Checked {vehicles.count()} vehicles"


@shared_task
def check_attendance_alerts():
    """Check and create attendance alerts"""
    from apps.students.models import Student
    from apps.attendance.models import AttendanceAlert
    
    active_students = Student.objects.filter(is_active=True)
    
    alerts_created = 0
    for student in active_students:
        try:
            AttendanceAlert.check_and_create_alerts(student)
            alerts_created += 1
        except Exception as e:
            logger.error(f"Error checking alerts for student {student.id}: {e}")
    
    logger.info(f"Checked attendance alerts for {active_students.count()} students")
    return f"Checked {active_students.count()} students, created alerts"


@shared_task
def cleanup_old_notifications():
    """Clean up old notifications"""
    from .models import Notification
    
    # Delete read notifications older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Deleted {deleted_count} old notifications")
    return f"Deleted {deleted_count} notifications"


@shared_task
def cleanup_old_location_logs():
    """Clean up old GPS location logs"""
    from apps.tracking.models import LocationLog
    
    # Delete logs older than 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count = LocationLog.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Deleted {deleted_count} old location logs")
    return f"Deleted {deleted_count} logs"


@shared_task
def send_scheduled_notifications():
    """Send scheduled bulk notifications"""
    from .models import BulkNotification
    
    now = timezone.now()
    
    scheduled = BulkNotification.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )
    
    for bulk_notification in scheduled:
        try:
            bulk_notification.status = 'sending'
            bulk_notification.save()
            
            # Get recipients
            from apps.authentication.models import User
            
            if bulk_notification.recipient_type == 'all_users':
                recipients = User.objects.filter(is_active=True)
            elif bulk_notification.recipient_type == 'all_parents':
                recipients = User.objects.filter(role='parent', is_active=True)
            elif bulk_notification.recipient_type == 'all_drivers':
                recipients = User.objects.filter(role='driver', is_active=True)
            elif bulk_notification.recipient_type == 'specific_users':
                recipients = User.objects.filter(
                    id__in=bulk_notification.recipient_ids,
                    is_active=True
                )
            
            bulk_notification.total_recipients = recipients.count()
            bulk_notification.save()
            
            # Send to each recipient
            from .models import Notification
            sent_count = 0
            failed_count = 0
            
            for user in recipients:
                try:
                    Notification.objects.create(
                        user=user,
                        title=bulk_notification.title,
                        message=bulk_notification.message,
                        notification_type=bulk_notification.notification_type,
                        sent_via='in_app'
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending to user {user.id}: {e}")
                    failed_count += 1
            
            bulk_notification.sent_count = sent_count
            bulk_notification.failed_count = failed_count
            bulk_notification.status = 'completed'
            bulk_notification.sent_at = timezone.now()
            bulk_notification.save()
            
            logger.info(f"Sent bulk notification {bulk_notification.id} to {sent_count} users")
            
        except Exception as e:
            logger.error(f"Error in bulk notification {bulk_notification.id}: {e}")
            bulk_notification.status = 'failed'
            bulk_notification.save()


@shared_task
def backup_database():
    """Create database backup"""
    from apps.backup.models import BackupLog
    from apps.authentication.models import User
    import subprocess
    import os
    from django.conf import settings
    
    backup_log = BackupLog.objects.create(
        backup_type='scheduled',
        status='in_progress',
        started_at=timezone.now()
    )
    
    try:
        # Create backup directory if not exists
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.sql'
        filepath = os.path.join(backup_dir, filename)
        
        # Execute pg_dump
        db_config = settings.DATABASES['default']
        command = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', db_config['PORT'],
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '-f', filepath
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        subprocess.run(command, env=env, check=True)
        
        # Get file size
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        backup_log.status = 'completed'
        backup_log.backup_path = filepath
        backup_log.file_name = filename
        backup_log.file_size_mb = file_size_mb
        backup_log.completed_at = timezone.now()
        backup_log.calculate_duration()
        backup_log.save()
        
        logger.info(f"Database backup completed: {filename}")
        return f"Backup completed: {filename}"
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        backup_log.status = 'failed'
        backup_log.error_message = str(e)
        backup_log.completed_at = timezone.now()
        backup_log.save()
        
        return f"Backup failed: {str(e)}"


@shared_task
def calculate_driver_ratings():
    """Calculate and update driver ratings"""
    from apps.authentication.models import Driver
    from apps.tracking.models import Trip
    from django.db.models import Avg
    
    drivers = Driver.objects.filter(user__is_active=True)
    
    for driver in drivers:
        # Calculate average from trip performance
        avg_rating = Trip.objects.filter(
            driver=driver,
            status='completed'
        ).aggregate(
            avg=Avg('performance__driver_rating')
        )['avg']
        
        if avg_rating:
            driver.rating = avg_rating
            driver.save(update_fields=['rating'])
    
    logger.info(f"Updated ratings for {drivers.count()} drivers")
    return f"Updated {drivers.count()} driver ratings"


# Periodic tasks configuration
from celery.schedules import crontab

# Add to celery beat schedule in settings:
"""
CELERY_BEAT_SCHEDULE = {
    'send-daily-summary': {
        'task': 'apps.notifications.tasks.send_daily_summary',
        'schedule': crontab(hour=18, minute=0),  # 6 PM daily
    },
    'generate-daily-reports': {
        'task': 'apps.notifications.tasks.generate_daily_reports',
        'schedule': crontab(hour=23, minute=0),  # 11 PM daily
    },
    'check-vehicle-maintenance': {
        'task': 'apps.notifications.tasks.check_vehicle_maintenance',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
    },
    'check-attendance-alerts': {
        'task': 'apps.notifications.tasks.check_attendance_alerts',
        'schedule': crontab(hour=16, minute=0),  # 4 PM daily
    },
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'cleanup-old-location-logs': {
        'task': 'apps.notifications.tasks.cleanup_old_location_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
    },
    'send-scheduled-notifications': {
        'task': 'apps.notifications.tasks.send_scheduled_notifications',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'backup-database': {
        'task': 'apps.notifications.tasks.backup_database',
        'schedule': crontab(hour=1, minute=0),  # 1 AM daily
    },
    'calculate-driver-ratings': {
        'task': 'apps.notifications.tasks.calculate_driver_ratings',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),  # Sunday midnight
    },
}
"""