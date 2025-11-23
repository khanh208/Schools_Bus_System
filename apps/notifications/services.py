from .models import Notification
from .realtime_service import RealtimeNotificationService

class NotificationService:
    @staticmethod
    def send_from_template(user, template_code, context, channels=None):
        """
        Hàm giả lập gửi thông báo từ template.
        Trong thực tế sẽ render nội dung dựa trên template_code.
        """
        if channels is None:
            channels = ['in_app']

        title = "Thông báo hệ thống"
        message = "Nội dung thông báo"

        # Logic map template_code sang nội dung (Ví dụ đơn giản)
        if template_code == 'DAILY_SUMMARY':
            title = f"Báo cáo ngày {context.get('date')}"
            message = (
                f"Tổng chuyến: {context.get('report').total_trips}. "
                f"Đúng giờ: {context.get('report').on_time_percentage}%"
            )
        elif template_code == 'MAINTENANCE_REMINDER':
            title = "Nhắc nhở bảo trì"
            message = f"Xe {context.get('vehicle').plate_number} cần bảo trì."
        elif template_code == 'ATTENDANCE_ALERT':
            title = "Cảnh báo điểm danh"
            message = f"Học sinh {context.get('student').full_name} vắng mặt không phép."

        # 1. Gửi In-App Notification
        if 'in_app' in channels:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='info'
            )
            # Gửi socket realtime
            RealtimeNotificationService.send_to_user(user.id, 'notification', {
                'title': title,
                'message': message
            })

        # 2. Gửi Email (Giả lập)
        if 'email' in channels:
            print(f"--- [MOCK EMAIL] To: {user.email} | Subject: {title} | Body: {message}")

        return True