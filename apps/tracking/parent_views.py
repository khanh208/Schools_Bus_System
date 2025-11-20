# apps/tracking/parent_views.py
# apps/tracking/parent_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
from asgiref.sync import sync_to_async  # ← THÊM import này

from .models import Trip, LocationLog
from apps.students.models import Student
from apps.routes.models import StudentRoute
from .serializers import TripDetailSerializer, LocationLogSerializer
from utils.permissions import IsParent


class ParentTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for parent to track their children's trips
    """
    permission_classes = [IsAuthenticated, IsParent]
    serializer_class = TripDetailSerializer
    
    def get_queryset(self):
        """Get trips for routes where parent's children are assigned"""
        user = self.request.user
        
        if not hasattr(user, 'parent_profile'):
            return Trip.objects.none()
        
        # Get student IDs
        student_ids = user.parent_profile.students.filter(
            is_active=True
        ).values_list('id', flat=True)
        
        # Get route IDs where students are assigned
        route_ids = StudentRoute.objects.filter(
            student_id__in=student_ids,
            is_active=True
        ).values_list('route_id', flat=True).distinct()
        
        # Get trips for today on those routes
        today = timezone.now().date()
        
        return Trip.objects.filter(
            route_id__in=route_ids,
            trip_date=today
        ).select_related('route', 'driver__user', 'vehicle')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active trips for parent's children"""
        trips = self.get_queryset().filter(
            status__in=['scheduled', 'in_progress']
        )
        
        serializer = self.get_serializer(trips, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def live_location(self, request, pk=None):
        """Get live location of trip"""
        trip = self.get_object()
        
        # Get latest location
        latest_log = trip.location_logs.order_by('-timestamp').first()
        
        if not latest_log:
            return Response({
                'message': 'No location data available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get recent path (last 20 points)
        recent_logs = trip.location_logs.order_by('-timestamp')[:20]
        
        return Response({
            'trip_id': trip.id,
            'current_location': {
                'lat': latest_log.location.y,
                'lng': latest_log.location.x,
                'speed': float(latest_log.speed) if latest_log.speed else 0,
                'timestamp': latest_log.timestamp.isoformat(),
                'accuracy': float(latest_log.accuracy) if latest_log.accuracy else None
            },
            'recent_path': [
                {
                    'lat': log.location.y,
                    'lng': log.location.x,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in recent_logs
            ],
            'trip_status': trip.status,
            'driver': {
                'name': trip.driver.user.full_name,
                'phone': trip.driver.user.phone
            },
            'vehicle': {
                'plate_number': trip.vehicle.plate_number,
                'type': trip.vehicle.vehicle_type
            }
        })
    
    @action(detail=False, methods=['get'])
    def my_children_status(self, request):
        """Get status of all parent's children"""
        user = request.user
        
        if not hasattr(user, 'parent_profile'):
            return Response({
                'error': 'Not a parent user'
            }, status=status.HTTP_403_FORBIDDEN)
        
        children = user.parent_profile.students.filter(is_active=True)
        today = timezone.now().date()
        
        children_data = []
        
        for child in children:
            # Get today's attendance
            from apps.attendance.models import Attendance
            attendance_today = Attendance.objects.filter(
                student=child,
                trip__trip_date=today
            ).select_related('trip').order_by('-check_time').first()
            
            # Get route assignment
            route_assignment = StudentRoute.objects.filter(
                student=child,
                is_active=True
            ).select_related('route', 'stop').first()
            
            # Get current trip
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
                'student_code': child.student_code,
                'class': child.class_obj.name if child.class_obj else None,
                'photo': child.photo.url if child.photo else None,
                'attendance_today': {
                    'status': attendance_today.get_status_display() if attendance_today else None,
                    'type': attendance_today.get_attendance_type_display() if attendance_today else None,
                    'time': attendance_today.check_time.isoformat() if attendance_today and attendance_today.check_time else None,
                    'location': {
                        'lat': attendance_today.location.y if attendance_today and attendance_today.location else None,
                        'lng': attendance_today.location.x if attendance_today and attendance_today.location else None
                    } if attendance_today and attendance_today.location else None
                } if attendance_today else None,
                'route': {
                    'id': route_assignment.route.id,
                    'code': route_assignment.route.route_code,
                    'name': route_assignment.route.route_name,
                    'stop': {
                        'id': route_assignment.stop.id,
                        'name': route_assignment.stop.stop_name,
                        'lat': route_assignment.stop.location.y,
                        'lng': route_assignment.stop.location.x
                    }
                } if route_assignment else None,
                'current_trip': {
                    'id': current_trip.id,
                    'status': current_trip.get_status_display(),
                    'scheduled_start': current_trip.scheduled_start_time.isoformat(),
                    'actual_start': current_trip.actual_start_time.isoformat() if current_trip.actual_start_time else None
                } if current_trip else None
            })
        
        return Response({
            'children': children_data,
            'total': len(children_data)
        })
    
    @action(detail=True, methods=['get'])
    def eta(self, request, pk=None):
        """Get ETA for parent's child's stop"""
        trip = self.get_object()
        student_id = request.query_params.get('student_id')
        
        if not student_id:
            return Response({
                'error': 'student_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify student belongs to parent
        try:
            student = Student.objects.get(
                id=student_id,
                parent=request.user.parent_profile
            )
        except Student.DoesNotExist:
            return Response({
                'error': 'Student not found or not yours'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get student's stop assignment
        assignment = StudentRoute.objects.filter(
            student=student,
            route=trip.route,
            is_active=True
        ).first()
        
        if not assignment:
            return Response({
                'error': 'Student not assigned to this route'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate ETA
        from apps.routes.services import ETAService
        eta = ETAService.calculate_eta(trip, assignment.stop)
        
        if not eta:
            return Response({
                'error': 'Cannot calculate ETA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        minutes_remaining = (eta - timezone.now()).total_seconds() / 60
        
        return Response({
            'student': {
                'id': student.id,
                'name': student.full_name
            },
            'stop': {
                'id': assignment.stop.id,
                'name': assignment.stop.stop_name,
                'lat': assignment.stop.location.y,
                'lng': assignment.stop.location.x
            },
            'eta': eta.isoformat(),
            'minutes_remaining': round(minutes_remaining, 1),
            'estimated_arrival_time': eta.strftime('%H:%M')
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_tracking_page(request):
    """Render parent tracking page - SYNC version"""
    return render(request, 'tracking/parent_tracking.html', {
        'user': request.user,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def parent_tracking_demo(request):
    """Demo page for parent tracking (no auth required) - SYNC version"""
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚌 Parent Tracking Demo</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            
            .container {
                display: flex;
                height: calc(100vh - 80px);
            }
            
            .sidebar {
                width: 350px;
                background: white;
                padding: 20px;
                overflow-y: auto;
                box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            }
            
            #map {
                flex: 1;
                height: 100%;
            }
            
            .info-card {
                background: #f0f4ff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
            }
            
            .status-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                background: #d1fae5;
                color: #065f46;
            }
            
            .btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
                font-weight: 600;
            }
            
            .btn:hover {
                background: #5568d3;
            }
            
            @media (max-width: 768px) {
                .container { flex-direction: column; }
                .sidebar { width: 100%; height: 40%; }
                #map { height: 60%; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚌 Theo dõi xe đưa đón - Demo</h1>
            <p>Không cần đăng nhập</p>
        </div>
        
        <div class="container">
            <div class="sidebar">
                <h3>📍 Thông tin Demo</h3>
                <div class="info-card">
                    <h4>Trạng thái hệ thống</h4>
                    <p>Server: <span class="status-badge" id="serverStatus">Đang kiểm tra...</span></p>
                    <p>WebSocket: <span class="status-badge" id="wsStatus">Chưa kết nối</span></p>
                </div>
                
                <div class="info-card">
                    <h4>🚌 Demo Trip</h4>
                    <p><strong>Tuyến:</strong> R001 - Tuyến 1</p>
                    <p><strong>Tài xế:</strong> Phạm Văn C</p>
                    <p><strong>Biển số:</strong> 51A-12345</p>
                    <p><strong>Trạng thái:</strong> <span class="status-badge">Đang chạy</span></p>
                </div>
                
                <div class="info-card">
                    <h4>⏱️ ETA</h4>
                    <p style="font-size: 24px; font-weight: bold; color: #667eea;">~15 phút</p>
                    <p style="font-size: 12px; color: #666;">Đến điểm dừng tiếp theo</p>
                </div>
                
                <button class="btn" onclick="testAPI()">🔍 Test API</button>
                <button class="btn" onclick="testWebSocket()">🔌 Test WebSocket</button>
                
                <div style="margin-top: 20px; padding: 10px; background: #fff3cd; border-radius: 4px;">
                    <small>💡 Đây là trang demo. Để sử dụng đầy đủ, vui lòng đăng nhập.</small>
                </div>
            </div>
            
            <div id="map"></div>
        </div>
        
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            // Initialize map
            const map = L.map('map').setView([10.8231, 106.6297], 13);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            // Add demo marker
            const busIcon = L.divIcon({
                html: '🚌',
                className: 'bus-marker',
                iconSize: [30, 30]
            });
            
            const busMarker = L.marker([10.8231, 106.6297], {icon: busIcon})
                .addTo(map)
                .bindPopup('<b>Demo Bus Location</b><br>TP. Hồ Chí Minh');
            
            // Add route stops
            const stops = [
                {lat: 10.8231, lng: 106.6297, name: 'Điểm 1'},
                {lat: 10.8331, lng: 106.6397, name: 'Điểm 2'},
                {lat: 10.8431, lng: 106.6497, name: 'Trường học'}
            ];
            
            stops.forEach(stop => {
                L.marker([stop.lat, stop.lng])
                    .addTo(map)
                    .bindPopup(stop.name);
            });
            
            // Draw route line
            const routeLine = stops.map(s => [s.lat, s.lng]);
            L.polyline(routeLine, {
                color: '#667eea',
                weight: 4,
                opacity: 0.7
            }).addTo(map);
            
            // Test API
            function testAPI() {
                fetch('/api/tracking/trips/')
                    .then(res => res.json())
                    .then(data => {
                        document.getElementById('serverStatus').textContent = 'Hoạt động ✓';
                        alert('✓ API connected!\\nFound ' + (data.count || 0) + ' trips');
                    })
                    .catch(err => {
                        document.getElementById('serverStatus').textContent = 'Lỗi ✗';
                        alert('✗ API error: ' + err.message);
                    });
            }
            
            // Test WebSocket
            function testWebSocket() {
                const ws = new WebSocket('ws://localhost:8000/ws/notifications/');
                
                ws.onopen = () => {
                    document.getElementById('wsStatus').textContent = 'Kết nối ✓';
                    alert('✓ WebSocket connected!');
                    ws.close();
                };
                
                ws.onerror = (err) => {
                    document.getElementById('wsStatus').textContent = 'Lỗi ✗';
                    alert('✗ WebSocket error: ' + err);
                };
            }
            
            // Auto test on load
            setTimeout(testAPI, 1000);
            
            console.log('Demo page loaded successfully');
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content)