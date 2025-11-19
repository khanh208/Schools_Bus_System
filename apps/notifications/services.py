# apps/notifications/services.py
"""
Notification services for sending notifications via various channels
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification, NotificationTemplate, NotificationLog, PushToken
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling all notification operations"""
    
    @staticmethod
    def send_notification(user, title, message, notification_type='info', 
                         channels=None, related_object=None, action_url=None):
        """
        Send notification to user via specified channels
        
        Args:
            user: User object
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, alert, success)
            channels: List of channels ['push', 'email', 'sms', 'in_app']
            related_object: Related model instance
            action_url: URL for notification action
        """
        if channels is None:
            channels = ['in_app', 'push']
        
        # Check user preferences
        if hasattr(user, 'notification_preferences'):
            prefs = user.notification_preferences
            
            # Filter channels based on preferences
            if 'push' in channels and not prefs.enable_push:
                channels.remove('push')
            if 'email' in channels and not prefs.enable_email:
                channels.remove('email')
            if 'sms' in channels and not prefs.enable_sms:
                channels.remove('sms')
            if 'in_app' in channels and not prefs.enable_in_app:
                channels.remove('in_app')
            
            # Check quiet hours
            if prefs.is_quiet_time():
                channels = ['in_app']  # Only in-app during quiet hours
        
        # Create in-app notification
        notification = None
        if 'in_app' in channels:
            content_type = None
            object_id = None
            
            if related_object:
                from django.contrib.contenttypes.models import ContentType
                content_type = ContentType.objects.get_for_model(related_object)
                object_id = related_object.id
            
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                sent_via='in_app',
                content_type=content_type,
                object_id=object_id,
                action_url=action_url
            )
        
        # Send push notification
        if 'push' in channels:
            NotificationService._send_push(user, title, message, notification)
        
        # Send email
        if 'email' in channels:
            NotificationService._send_email(user, title, message, notification)
        
        # Send SMS
        if 'sms' in channels:
            NotificationService._send_sms(user, title, message, notification)
        
        return notification
    
    @staticmethod
    def _send_push(user, title, message, notification=None):
        """Send push notification via FCM"""
        try:
            # Get active push tokens for user
            tokens = PushToken.objects.filter(
                user=user,
                is_active=True
            )
            
            if not tokens.exists():
                logger.warning(f"No push tokens found for user {user.username}")
                return
            
            # Send via Firebase (placeholder - implement actual FCM logic)
            for token in tokens:
                try:
                    # TODO: Implement actual FCM sending
                    # firebase_admin.messaging.send(...)
                    
                    NotificationLog.objects.create(
                        notification=notification,
                        user=user,
                        channel='push',
                        status='sent',
                        recipient=token.token[:50],
                        sent_at=timezone.now()
                    )
                    
                    token.last_used = timezone.now()
                    token.save(update_fields=['last_used'])
                    
                except Exception as e:
                    logger.error(f"Error sending push to token {token.id}: {e}")
                    NotificationLog.objects.create(
                        notification=notification,
                        user=user,
                        channel='push',
                        status='failed',
                        recipient=token.token[:50],
                        error_message=str(e),
                        failed_at=timezone.now()
                    )
        
        except Exception as e:
            logger.error(f"Error in _send_push: {e}")
    
    @staticmethod
    def _send_email(user, title, message, notification=None):
        """Send email notification"""
        try:
            if not user.email:
                logger.warning(f"No email for user {user.username}")
                return
            
            # Render email template
            context = {
                'user': user,
                'title': title,
                'message': message,
                'notification': notification
            }
            
            html_message = render_to_string(
                'notifications/email_notification.html',
                context
            )
            
            # Send email
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            NotificationLog.objects.create(
                notification=notification,
                user=user,
                channel='email',
                status='sent',
                recipient=user.email,
                sent_at=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")
            NotificationLog.objects.create(
                notification=notification,
                user=user,
                channel='email',
                status='failed',
                recipient=user.email,
                error_message=str(e),
                failed_at=timezone.now()
            )
    
    @staticmethod
    def _send_sms(user, title, message, notification=None):
        """Send SMS notification via Twilio"""
        try:
            if not user.phone:
                logger.warning(f"No phone for user {user.username}")
                return
            
            # TODO: Implement Twilio SMS sending
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(...)
            
            NotificationLog.objects.create(
                notification=notification,
                user=user,
                channel='sms',
                status='sent',
                recipient=user.phone,
                sent_at=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error sending SMS to {user.phone}: {e}")
            NotificationLog.objects.create(
                notification=notification,
                user=user,
                channel='sms',
                status='failed',
                recipient=user.phone,
                error_message=str(e),
                failed_at=timezone.now()
            )
    
    @staticmethod
    def send_from_template(template_code, user, context, channels=None):
        """Send notification from template"""
        try:
            template = NotificationTemplate.objects.get(
                code=template_code,
                is_active=True
            )
            
            title, message = template.render(context)
            
            if channels is None:
                channels = []
                if template.send_push:
                    channels.append('push')
                if template.send_email:
                    channels.append('email')
                if template.send_sms:
                    channels.append('sms')
                if template.send_in_app:
                    channels.append('in_app')
            
            return NotificationService.send_notification(
                user=user,
                title=title,
                message=message,
                notification_type=template.notification_type,
                channels=channels
            )
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template {template_code} not found")
            return None
    
    @staticmethod
    def send_trip_notification(trip, notification_type, **kwargs):
        """Send trip-related notifications"""
        from apps.routes.models import StudentRoute
        
        # Get parents of students on this trip
        student_ids = StudentRoute.objects.filter(
            route=trip.route,
            is_active=True
        ).values_list('student_id', flat=True)
        
        from apps.students.models import Student
        parents = Student.objects.filter(
            id__in=student_ids,
            is_active=True
        ).values_list('parent__user', flat=True).distinct()
        
        from apps.authentication.models import User
        parent_users = User.objects.filter(id__in=parents)
        
        templates = {
            'trip_started': 'TRIP_STARTED',
            'trip_completed': 'TRIP_COMPLETED',
            'trip_delayed': 'TRIP_DELAYED',
            'trip_cancelled': 'TRIP_CANCELLED',
        }
        
        template_code = templates.get(notification_type)
        if not template_code:
            return
        
        context = {
            'trip': trip,
            'route': trip.route,
            'driver': trip.driver,
            **kwargs
        }
        
        for user in parent_users:
            NotificationService.send_from_template(
                template_code=template_code,
                user=user,
                context=context
            )
    
    @staticmethod
    def send_attendance_notification(attendance):
        """Send attendance notification to parent"""
        parent_user = attendance.student.parent.user
        
        context = {
            'student': attendance.student,
            'attendance': attendance,
            'trip': attendance.trip,
            'stop': attendance.stop
        }
        
        template_code = f"ATTENDANCE_{attendance.attendance_type.upper()}"
        
        NotificationService.send_from_template(
            template_code=template_code,
            user=parent_user,
            context=context
        )
    
    @staticmethod
    def send_eta_notification(trip, stop, eta_minutes):
        """Send ETA notification to parents"""
        from apps.routes.models import StudentRoute
        
        # Get students for this stop
        student_ids = StudentRoute.objects.filter(
            route=trip.route,
            stop=stop,
            is_active=True
        ).values_list('student_id', flat=True)
        
        from apps.students.models import Student
        parents = Student.objects.filter(
            id__in=student_ids,
            is_active=True
        ).values_list('parent__user', flat=True).distinct()
        
        from apps.authentication.models import User
        parent_users = User.objects.filter(id__in=parents)
        
        context = {
            'trip': trip,
            'stop': stop,
            'eta_minutes': eta_minutes,
            'estimated_arrival': timezone.now() + timezone.timedelta(minutes=eta_minutes)
        }
        
        for user in parent_users:
            NotificationService.send_from_template(
                template_code='ETA_UPDATE',
                user=user,
                context=context,
                channels=['push', 'in_app']
            )