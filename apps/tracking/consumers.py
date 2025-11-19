import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.gis.geos import Point
from django.utils import timezone
from decimal import Decimal


class TripTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer cho real-time tracking xe bus"""
    
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.trip_group_name = f'trip_{self.trip_id}'
        
        # Join trip group
        await self.channel_layer.group_add(
            self.trip_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial trip data
        trip_data = await self.get_trip_data()
        if trip_data:
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': trip_data
            }))
    
    async def disconnect(self, close_code):
        # Leave trip group
        await self.channel_layer.group_discard(
            self.trip_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Nhận message từ WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'location_update':
                # Driver gửi vị trí mới
                await self.handle_location_update(data)
            
            elif message_type == 'request_eta':
                # Parent yêu cầu ETA
                await self.send_eta_update(data.get('stop_id'))
            
            elif message_type == 'ping':
                # Keep alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
        
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_location_update(self, data):
        """Xử lý cập nhật vị trí từ driver"""
        location_data = await self.save_location(data)
        
        # Broadcast to all clients in trip group
        await self.channel_layer.group_send(
            self.trip_group_name,
            {
                'type': 'location_broadcast',
                'location': location_data
            }
        )
        
        # Kiểm tra gần điểm dừng và gửi ETA
        await self.check_nearby_stops(location_data)
    
    async def location_broadcast(self, event):
        """Gửi location update đến WebSocket client"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'data': event['location']
        }))
    
    async def stop_arrival_broadcast(self, event):
        """Gửi thông báo xe đến điểm dừng"""
        await self.send(text_data=json.dumps({
            'type': 'stop_arrival',
            'data': event['arrival']
        }))
    
    async def eta_broadcast(self, event):
        """Gửi ETA update"""
        await self.send(text_data=json.dumps({
            'type': 'eta_update',
            'data': event['eta']
        }))
    
    async def attendance_broadcast(self, event):
        """Gửi thông báo điểm danh"""
        await self.send(text_data=json.dumps({
            'type': 'attendance_update',
            'data': event['attendance']
        }))
    
    async def notification_broadcast(self, event):
        """Gửi thông báo chung"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['notification']
        }))
    
    @database_sync_to_async
    def get_trip_data(self):
        """Lấy thông tin trip ban đầu"""
        from .models import Trip
        from apps.routes.models import RouteStop
        
        try:
            trip = Trip.objects.select_related(
                'route', 'driver__user', 'vehicle'
            ).get(id=self.trip_id)
            
            # Lấy danh sách stops
            stops = RouteStop.objects.filter(
                route=trip.route,
                is_active=True
            ).order_by('stop_order')
            
            # Lấy vị trí hiện tại
            latest_log = trip.location_logs.order_by('-timestamp').first()
            
            return {
                'trip_id': trip.id,
                'route': {
                    'code': trip.route.route_code,
                    'name': trip.route.route_name,
                },
                'vehicle': {
                    'plate': trip.vehicle.plate_number,
                    'type': trip.vehicle.vehicle_type,
                },
                'driver': {
                    'name': trip.driver.user.full_name,
                    'phone': trip.driver.user.phone,
                },
                'status': trip.status,
                'current_location': {
                    'lat': latest_log.location.y if latest_log else None,
                    'lng': latest_log.location.x if latest_log else None,
                    'speed': float(latest_log.speed) if latest_log and latest_log.speed else 0,
                    'timestamp': latest_log.timestamp.isoformat() if latest_log else None,
                } if latest_log else None,
                'stops': [
                    {
                        'id': stop.id,
                        'name': stop.stop_name,
                        'order': stop.stop_order,
                        'lat': stop.location.y,
                        'lng': stop.location.x,
                        'estimated_arrival': stop.estimated_arrival.isoformat() if stop.estimated_arrival else None,
                    }
                    for stop in stops
                ],
                'students': trip.total_students,
                'checked_in': trip.checked_in_students,
            }
        except Trip.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_location(self, data):
        """Lưu location log vào database"""
        from .models import Trip, LocationLog
        
        try:
            trip = Trip.objects.get(id=self.trip_id)
            
            location = Point(
                float(data.get('lng')),
                float(data.get('lat'))
            )
            
            log = LocationLog.objects.create(
                trip=trip,
                driver=trip.driver,
                location=location,
                speed=data.get('speed'),
                heading=data.get('heading'),
                accuracy=data.get('accuracy'),
                battery_level=data.get('battery_level'),
                timestamp=timezone.now()
            )
            
            return {
                'id': log.id,
                'lat': log.location.y,
                'lng': log.location.x,
                'speed': float(log.speed) if log.speed else 0,
                'heading': float(log.heading) if log.heading else 0,
                'timestamp': log.timestamp.isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    @database_sync_to_async
    def check_nearby_stops(self, location_data):
        """Kiểm tra xe gần điểm dừng nào và tính ETA"""
        from .models import Trip, StopArrival
        from apps.routes.models import RouteStop
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import D
        
        try:
            trip = Trip.objects.get(id=self.trip_id)
            current_location = Point(location_data['lng'], location_data['lat'])
            
            # Lấy các điểm dừng chưa đến
            completed_stops = StopArrival.objects.filter(
                trip=trip,
                actual_arrival__isnull=False
            ).values_list('stop_id', flat=True)
            
            remaining_stops = RouteStop.objects.filter(
                route=trip.route,
                is_active=True
            ).exclude(id__in=completed_stops).order_by('stop_order')
            
            # Kiểm tra điểm dừng tiếp theo
            next_stop = remaining_stops.first()
            if next_stop:
                distance = current_location.distance(next_stop.location) * 111  # km
                
                # Nếu gần (< 500m), gửi thông báo
                if distance < 0.5:
                    # Gửi thông báo đến phụ huynh có con ở điểm dừng này
                    from apps.routes.models import StudentRoute
                    students = StudentRoute.objects.filter(
                        route=trip.route,
                        stop=next_stop,
                        is_active=True
                    ).select_related('student__parent__user')
                    
                    for assignment in students:
                        # Gửi đến group của parent
                        parent_group = f'user_{assignment.student.parent.user.id}'
                        from channels.layers import get_channel_layer
                        channel_layer = get_channel_layer()
                        
                        from asgiref.sync import async_to_sync
                        async_to_sync(channel_layer.group_send)(
                            parent_group,
                            {
                                'type': 'notification_broadcast',
                                'notification': {
                                    'title': '🚌 Xe sắp đến!',
                                    'message': f'Xe bus sẽ đến điểm {next_stop.stop_name} trong vài phút nữa.',
                                    'student': assignment.student.full_name,
                                    'stop': next_stop.stop_name,
                                    'distance': round(distance, 2),
                                }
                            }
                        )
        except Exception as e:
            print(f"Error checking nearby stops: {e}")
    
    async def send_eta_update(self, stop_id):
        """Tính và gửi ETA cho điểm dừng"""
        eta_data = await self.calculate_eta(stop_id)
        
        if eta_data:
            await self.send(text_data=json.dumps({
                'type': 'eta_update',
                'data': eta_data
            }))
    
    @database_sync_to_async
    def calculate_eta(self, stop_id):
        """Tính ETA đến điểm dừng"""
        from .models import Trip
        from apps.routes.models import RouteStop
        from apps.routes.services import ETAService
        
        try:
            trip = Trip.objects.get(id=self.trip_id)
            stop = RouteStop.objects.get(id=stop_id)
            
            eta = ETAService.calculate_eta(trip, stop)
            
            return {
                'stop_id': stop_id,
                'stop_name': stop.stop_name,
                'eta': eta.isoformat(),
                'minutes_remaining': round((eta - timezone.now()).total_seconds() / 60, 1)
            }
        except Exception as e:
            return {'error': str(e)}


class ParentNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer cho thông báo real-time đến phụ huynh"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        if self.user.role != 'parent':
            await self.close()
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        # Join user notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Gửi thông báo chào mừng
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': f'Chào {self.user.full_name}! Đã kết nối thành công.',
            'timestamp': timezone.now().isoformat()
        }))
        
        # Gửi thông báo chưa đọc
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Nhận message từ client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            
            elif message_type == 'get_children_status':
                children_status = await self.get_children_status()
                await self.send(text_data=json.dumps({
                    'type': 'children_status',
                    'data': children_status
                }))
        
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def notification_broadcast(self, event):
        """Gửi thông báo đến client"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['notification']
        }))
    
    async def attendance_broadcast(self, event):
        """Gửi cập nhật điểm danh"""
        await self.send(text_data=json.dumps({
            'type': 'attendance',
            'data': event['attendance']
        }))
    
    async def trip_update_broadcast(self, event):
        """Gửi cập nhật chuyến đi"""
        await self.send(text_data=json.dumps({
            'type': 'trip_update',
            'data': event['trip']
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """Đếm số thông báo chưa đọc"""
        from apps.notifications.models import Notification
        
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Đánh dấu thông báo đã đọc"""
        from apps.notifications.models import Notification
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_children_status(self):
        """Lấy trạng thái của các con"""
        from apps.students.models import Student
        from apps.tracking.models import Trip
        from apps.attendance.models import Attendance
        
        children = Student.objects.filter(
            parent__user=self.user,
            is_active=True
        ).select_related('class_obj')
        
        children_data = []
        today = timezone.now().date()
        
        for child in children:
            # Lấy attendance hôm nay
            today_attendance = Attendance.objects.filter(
                student=child,
                trip__trip_date=today
            ).order_by('-check_time').first()
            
            # Lấy route assignment
            from apps.routes.models import StudentRoute
            route_assignment = StudentRoute.objects.filter(
                student=child,
                is_active=True
            ).select_related('route', 'stop').first()
            
            # Lấy trip hiện tại
            current_trip = None
            if route_assignment:
                current_trip = Trip.objects.filter(
                    route=route_assignment.route,
                    trip_date=today,
                    status__in=['scheduled', 'in_progress']
                ).first()
            
            children_data.append({
                'student_id': child.id,
                'name': child.full_name,
                'class': child.class_obj.name if child.class_obj else None,
                'attendance_today': {
                    'status': today_attendance.get_status_display() if today_attendance else None,
                    'time': today_attendance.check_time.isoformat() if today_attendance and today_attendance.check_time else None,
                } if today_attendance else None,
                'route': {
                    'code': route_assignment.route.route_code if route_assignment else None,
                    'stop': route_assignment.stop.stop_name if route_assignment else None,
                } if route_assignment else None,
                'current_trip': {
                    'id': current_trip.id,
                    'status': current_trip.get_status_display(),
                } if current_trip else None,
            })
        
        return children_data