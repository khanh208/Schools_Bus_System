from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class RealtimeNotificationService:
    """Service để gửi thông báo real-time qua WebSocket"""
    
    @staticmethod
    def send_to_user(user_id, notification_type, data):
        """
        Gửi thông báo đến một user cụ thể
        
        Args:
            user_id: ID của user
            notification_type: Loại thông báo (notification, attendance, trip_update)
            data: Dữ liệu thông báo
        """
        channel_layer = get_channel_layer()
        group_name = f'user_{user_id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': f'{notification_type}_broadcast',
                notification_type: data
            }
        )
    
    @staticmethod
    def send_attendance_notification(attendance):
        """Gửi thông báo điểm danh đến phụ huynh"""
        parent_id = attendance.student.parent.user.id
        
        data = {
            'title': f'Điểm danh: {attendance.student.full_name}',
            'message': f'Con em {attendance.get_status_display()} lúc {attendance.check_time.strftime("%H:%M")}',
            'student': {
                'id': attendance.student.id,
                'name': attendance.student.full_name,
                'photo': attendance.student.photo.url if attendance.student.photo else None,
            },
            'attendance': {
                'type': attendance.get_attendance_type_display(),
                'status': attendance.get_status_display(),
                'time': attendance.check_time.isoformat() if attendance.check_time else None,
                'temperature': float(attendance.temperature) if attendance.temperature else None,
            },
            'trip': {
                'route_code': attendance.trip.route.route_code,
                'route_name': attendance.trip.route.route_name,
            }
        }
        
        RealtimeNotificationService.send_to_user(parent_id, 'attendance', data)
    
    @staticmethod
    def send_trip_update(trip, message):
        """Gửi cập nhật chuyến đi đến tất cả phụ huynh có con trên tuyến"""
        from apps.routes.models import StudentRoute
        
        # Lấy danh sách phụ huynh
        assignments = StudentRoute.objects.filter(
            route=trip.route,
            is_active=True
        ).select_related('student__parent__user')
        
        parent_ids = set(a.student.parent.user.id for a in assignments)
        
        data = {
            'title': f'Cập nhật: {trip.route.route_code}',
            'message': message,
            'trip': {
                'id': trip.id,
                'status': trip.get_status_display(),
                'route_code': trip.route.route_code,
                'route_name': trip.route.route_name,
            }
        }
        
        for parent_id in parent_ids:
            RealtimeNotificationService.send_to_user(parent_id, 'trip_update', data)
    
    @staticmethod
    def send_eta_alert(trip, stop, eta_minutes):
        """Gửi cảnh báo ETA đến phụ huynh có con ở điểm dừng"""
        from apps.routes.models import StudentRoute
        
        assignments = StudentRoute.objects.filter(
            route=trip.route,
            stop=stop,
            is_active=True
        ).select_related('student__parent__user')
        
        for assignment in assignments:
            parent_id = assignment.student.parent.user.id
            
            data = {
                'title': '🚌 Xe sắp đến!',
                'message': f'Xe bus sẽ đến điểm {stop.stop_name} trong khoảng {eta_minutes} phút nữa.',
                'student': {
                    'name': assignment.student.full_name,
                },
                'stop': {
                    'name': stop.stop_name,
                    'eta_minutes': eta_minutes,
                },
                'trip': {
                    'route_code': trip.route.route_code,
                }
            }
            
            RealtimeNotificationService.send_to_user(parent_id, 'notification', data)
    
    @staticmethod
    def broadcast_to_trip(trip_id, message_type, data):
        """Broadcast message đến tất cả người đang theo dõi trip"""
        channel_layer = get_channel_layer()
        group_name = f'trip_{trip_id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': f'{message_type}_broadcast',
                message_type: data
            }
        )