import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.gis.geos import Point
from django.utils import timezone
from decimal import Decimal

# ============================================
# 1. CONSUMER CHO TÀI XẾ (Trip Tracking)
# ============================================
class TripTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer cho real-time tracking xe bus"""
    
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.trip_group_name = f'trip_{self.trip_id}'
        
        print(f"--- [TRIP WS] Connecting to Trip ID: {self.trip_id} ---")
        
        # 1. CHẤP NHẬN KẾT NỐI NGAY (Để frontend không bị lỗi đóng đột ngột)
        await self.accept()
        print("--- [TRIP WS] 🚀 ACCEPTED (Đã chấp nhận kết nối)")

        # 2. Kiểm tra User
        self.user = self.scope.get('user')
        if not self.user or self.user.is_anonymous:
            print("--- [TRIP WS] ❌ User chưa đăng nhập -> Đóng")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Unauthorized: Bạn chưa đăng nhập.'
            }))
            await self.close()
            return

        # 3. Thử Join Redis Group
        try:
            await self.channel_layer.group_add(
                self.trip_group_name,
                self.channel_name
            )
            print(f"--- [TRIP WS] ✅ Đã join group Redis: {self.trip_group_name}")
        except Exception as e:
            print(f"--- [TRIP WS] ⚠️ LỖI REDIS (Vẫn giữ kết nối): {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'warning',
                'message': 'Hệ thống real-time đang gặp sự cố, nhưng bạn vẫn có thể gửi vị trí.'
            }))

        # 4. Gửi dữ liệu chuyến đi ban đầu
        try:
            trip_data = await self.get_trip_data()
            if trip_data:
                await self.send(text_data=json.dumps({
                    'type': 'initial_data',
                    'data': trip_data
                }))
            else:
                print(f"--- [TRIP WS] ⚠️ Không tìm thấy dữ liệu Trip {self.trip_id}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Không tìm thấy thông tin chuyến đi này.'
                }))
        except Exception as e:
            print(f"--- [TRIP WS] Lỗi lấy dữ liệu: {e}")
            import traceback
            traceback.print_exc()
    
    async def disconnect(self, close_code):
        print(f"--- [TRIP WS] Disconnected: {close_code}")
        try:
            await self.channel_layer.group_discard(
                self.trip_group_name,
                self.channel_name
            )
        except:
            pass
    
    async def receive(self, text_data):
        """Nhận message từ WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'location_update':
                # Driver gửi vị trí mới
                await self.handle_location_update(data)
            
            elif message_type == 'ping':
                # Keep alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
        
        except Exception as e:
            print(f"--- [TRIP WS] Error receiving: {e}")
    
    async def handle_location_update(self, data):
        """Xử lý cập nhật vị trí từ driver"""
        try:
            # 1. Lưu vào DB
            location_data = await self.save_location(data)
            
            # 2. Gửi cho parent (qua Redis group)
            try:
                await self.channel_layer.group_send(
                    self.trip_group_name,
                    {
                        'type': 'location_broadcast',
                        'location': location_data
                    }
                )
            except Exception as e:
                print(f"--- [TRIP WS] Lỗi gửi Redis: {e}")

            # 3. Kiểm tra điểm dừng (Optional - bọc lỗi để không crash)
            try:
                await self.check_nearby_stops(location_data)
            except Exception as e:
                print(f"--- [TRIP WS] Lỗi check stops: {e}")

        except Exception as e:
             print(f"--- [TRIP WS] Lỗi xử lý location: {e}")
             import traceback
             traceback.print_exc()
    
    # Các hàm gửi message xuống client
    async def location_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'location_update', 'data': event['location'] }))
    
    async def stop_arrival_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'stop_arrival', 'data': event['arrival'] }))
    
    async def eta_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'eta_update', 'data': event['eta'] }))
    
    async def attendance_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'attendance_update', 'data': event['attendance'] }))
    
    async def notification_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'notification', 'data': event['notification'] }))
    
    @database_sync_to_async
    def get_trip_data(self):
        """Lấy thông tin trip ban đầu"""
        from .models import Trip
        from apps.routes.models import RouteStop
        
        try:
            trip = Trip.objects.select_related(
                'route', 'driver__user', 'vehicle'
            ).filter(id=self.trip_id).first()
            
            if not trip: return None
            
            stops = RouteStop.objects.filter(route=trip.route, is_active=True).order_by('stop_order')
            latest_log = trip.location_logs.order_by('-timestamp').first()
            
            stops_data = []
            for s in stops:
                 stops_data.append({
                    'id': s.id, 
                    'name': s.stop_name, 
                    'lat': s.location.y if s.location else 0, 
                    'lng': s.location.x if s.location else 0
                })

            return {
                'trip_id': trip.id,
                'route': {
                    'code': trip.route.route_code,
                    'name': trip.route.route_name,
                },
                'vehicle': {
                    'plate': trip.vehicle.plate_number,
                },
                'driver': {
                    'name': trip.driver.user.full_name,
                    'phone': trip.driver.user.phone,
                },
                'status': trip.status,
                'current_location': {
                    'lat': latest_log.location.y if latest_log and latest_log.location else None,
                    'lng': latest_log.location.x if latest_log and latest_log.location else None,
                } if latest_log else None,
                'stops': stops_data
            }
        except Exception as e:
            print(f"Error get_trip_data: {e}")
            return None
    
    @database_sync_to_async
    def save_location(self, data):
        """Lưu location log vào database"""
        from .models import Trip, LocationLog
        try:
            trip = Trip.objects.get(id=self.trip_id)
            location = Point(float(data.get('lng')), float(data.get('lat')))
            
            log = LocationLog.objects.create(
                trip=trip,
                driver=trip.driver,
                location=location,
                speed=data.get('speed', 0),
                timestamp=timezone.now()
            )
            return {'lat': log.location.y, 'lng': log.location.x, 'speed': float(log.speed) if log.speed else 0}
        except Exception as e:
            print(f"Error save_location: {e}")
            return {}

    @database_sync_to_async
    def check_nearby_stops(self, location_data):
        pass # Tạm thời bỏ trống logic phức tạp để tránh lỗi


# ============================================
# 2. CONSUMER CHO PHỤ HUYNH (Parent Notifications)
# ============================================
class ParentNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"--- [PARENT WS] Connecting... {self.channel_name}")
        
        # 1. CHẤP NHẬN KẾT NỐI NGAY
        await self.accept()
        print("--- [PARENT WS] 🚀 ACCEPTED")

        # 2. Kiểm tra User
        self.user = self.scope.get('user')
        
        if not self.user or self.user.is_anonymous:
            print("--- [PARENT WS] ❌ User chưa đăng nhập -> Đóng")
            await self.send(text_data=json.dumps({
                'type': 'error', 
                'message': 'Authentication required'
            }))
            await self.close()
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        # 3. Join Redis Group
        try:
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            print(f"--- [PARENT WS] ✅ Joined Group {self.user_group_name}")
        except Exception as e:
            print(f"--- [PARENT WS] ❌ Redis Error: {str(e)}")
        
        # 4. Gửi tin chào mừng
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': f'Chào {self.user.full_name}! Kết nối thành công.'
        }))

    async def disconnect(self, close_code):
        print(f"--- [PARENT WS] Disconnected: {close_code}")
        if hasattr(self, 'user_group_name'):
            try:
                await self.channel_layer.group_discard(self.user_group_name, self.channel_name)
            except: pass
            
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'get_children_status':
                children_status = await self.get_children_status()
                await self.send(text_data=json.dumps({
                    'type': 'children_status',
                    'data': children_status
                }))
        except Exception as e:
            print(f"--- [PARENT WS] Error receiving: {e}")

    async def notification_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'notification', 'data': event['notification'] }))
    
    async def attendance_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'attendance', 'data': event['attendance'] }))
    
    async def trip_update_broadcast(self, event):
        await self.send(text_data=json.dumps({ 'type': 'trip_update', 'data': event['trip'] }))

    @database_sync_to_async
    def get_children_status(self):
        """Lấy dữ liệu con cái (Bọc lỗi kỹ càng)"""
        from apps.students.models import Student
        from apps.tracking.models import Trip
        from apps.attendance.models import Attendance
        from apps.routes.models import StudentRoute
        
        try:
            children = Student.objects.filter(parent__user=self.user, is_active=True).select_related('class_obj')
            children_data = []
            today = timezone.now().date()
            
            for child in children:
                try:
                    today_attendance = Attendance.objects.filter(student=child, trip__trip_date=today).order_by('-check_time').first()
                    route_assignment = StudentRoute.objects.filter(student=child, is_active=True).select_related('route', 'stop').first()
                    
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
                        'class': child.class_obj.name if child.class_obj else 'N/A',
                        'attendance_today': {
                            'status': today_attendance.get_status_display() if today_attendance else None
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
                except Exception as e:
                    print(f"--- [PARENT WS] Lỗi child {child.id}: {e}")
                    continue
            
            return children_data
        except Exception as e:
            print(f"--- [PARENT WS] Lỗi query chính: {e}")
            return []