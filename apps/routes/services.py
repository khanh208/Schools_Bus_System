# apps/routes/services.py - IMPROVED VERSION
from django.contrib.gis.geos import Point, LineString
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
import math


class RouteOptimizationService:
    """✅ Cải thiện thuật toán tối ưu tuyến đường"""
    
    @staticmethod
    def haversine_distance(point1, point2):
        """
        Tính khoảng cách Haversine chính xác hơn
        
        Args:
            point1: Point(lng, lat) hoặc tuple (lng, lat)
            point2: Point(lng, lat) hoặc tuple (lng, lat)
        
        Returns:
            float: Khoảng cách (km)
        """
        if isinstance(point1, (list, tuple)):
            point1 = Point(point1[0], point1[1])
        if isinstance(point2, (list, tuple)):
            point2 = Point(point2[0], point2[1])
        
        lat1, lon1 = math.radians(point1.y), math.radians(point1.x)
        lat2, lon2 = math.radians(point2.y), math.radians(point2.x)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371 * c  # Bán kính Trái Đất
    
    @staticmethod
    def optimize_route_stops(route, school_location=None):
        """
        ✅ Tối ưu thứ tự điểm dừng bằng Nearest Neighbor + 2-opt
        
        Args:
            route: Route object
            school_location: Point - Vị trí trường học
        
        Returns:
            list: Danh sách điểm dừng đã tối ưu
        """
        from apps.routes.models import RouteStop
        
        stops = list(route.stops.filter(is_active=True))
        if len(stops) < 2:
            return stops
        
        # 1. NEAREST NEIGHBOR ALGORITHM
        if not school_location:
            school_location = stops[0].location
        
        optimized = []
        remaining = stops.copy()
        current = school_location
        
        while remaining:
            nearest = min(
                remaining,
                key=lambda s: RouteOptimizationService.haversine_distance(current, s.location)
            )
            optimized.append(nearest)
            remaining.remove(nearest)
            current = nearest.location
        
        # 2. 2-OPT IMPROVEMENT (Giảm đường đi chéo)
        improved = True
        while improved:
            improved = False
            for i in range(1, len(optimized) - 2):
                for j in range(i + 1, len(optimized)):
                    if j - i == 1:
                        continue
                    
                    # Tính khoảng cách hiện tại
                    current_dist = (
                        RouteOptimizationService.haversine_distance(
                            optimized[i-1].location if i > 0 else school_location,
                            optimized[i].location
                        ) +
                        RouteOptimizationService.haversine_distance(
                            optimized[j-1].location,
                            optimized[j].location if j < len(optimized) else school_location
                        )
                    )
                    
                    # Tính khoảng cách sau khi swap
                    new_dist = (
                        RouteOptimizationService.haversine_distance(
                            optimized[i-1].location if i > 0 else school_location,
                            optimized[j-1].location
                        ) +
                        RouteOptimizationService.haversine_distance(
                            optimized[i].location,
                            optimized[j].location if j < len(optimized) else school_location
                        )
                    )
                    
                    if new_dist < current_dist:
                        # Reverse segment
                        optimized[i:j] = reversed(optimized[i:j])
                        improved = True
        
        # 3. CẬP NHẬT THỨ TỰ VÀO DATABASE
        for idx, stop in enumerate(optimized, start=1):
            stop.stop_order = idx
            stop.save(update_fields=['stop_order'])
        
        # 4. CẬP NHẬT TỔNG QUÃNG ĐƯỜNG
        total_distance = sum(
            RouteOptimizationService.haversine_distance(
                optimized[i-1].location if i > 0 else school_location,
                stop.location
            )
            for i, stop in enumerate(optimized)
        )
        
        route.total_distance = round(total_distance, 2)
        route.save(update_fields=['total_distance'])
        
        return optimized
    
    @staticmethod
    def calculate_route_metrics(route):
        """
        ✅ Tính toán các chỉ số của tuyến đường
        
        Returns:
            dict: Các chỉ số (duration, distance, efficiency)
        """
        stops = route.stops.filter(is_active=True).order_by('stop_order')
        
        if stops.count() < 2:
            return {
                'total_distance': 0,
                'estimated_duration': 0,
                'average_speed': 25,
                'stops_count': stops.count()
            }
        
        # Tính tổng quãng đường
        total_distance = 0
        for i in range(len(stops) - 1):
            total_distance += RouteOptimizationService.haversine_distance(
                stops[i].location,
                stops[i + 1].location
            )
        
        # Tính thời gian dự kiến
        avg_speed = 25  # km/h trong thành phố
        travel_time = (total_distance / avg_speed) * 60  # phút
        
        # Thời gian dừng
        stop_time = sum(s.stop_duration or 2 for s in stops)
        
        total_duration = int(travel_time + stop_time)
        
        return {
            'total_distance': round(total_distance, 2),
            'estimated_duration': total_duration,
            'average_speed': avg_speed,
            'stops_count': len(stops),
            'travel_time': int(travel_time),
            'stop_time': stop_time
        }
    
    @staticmethod
    def check_route_feasibility(route):
        """
        ✅ Kiểm tra tính khả thi của tuyến đường
        
        Returns:
            dict: Kết quả kiểm tra
        """
        issues = []
        warnings = []
        
        # 1. Kiểm tra capacity
        from apps.routes.models import StudentRoute
        
        student_count = StudentRoute.objects.filter(
            route=route,
            is_active=True
        ).count()
        
        if route.vehicle:
            if student_count > route.vehicle.capacity:
                issues.append(f"Vượt sức chứa: {student_count}/{route.vehicle.capacity}")
            elif student_count > route.vehicle.capacity * 0.9:
                warnings.append(f"Gần đầy: {student_count}/{route.vehicle.capacity}")
        
        # 2. Kiểm tra thời gian
        metrics = RouteOptimizationService.calculate_route_metrics(route)
        if metrics['estimated_duration'] > 90:
            warnings.append(f"Tuyến quá dài: {metrics['estimated_duration']} phút")
        
        # 3. Kiểm tra tài xế và xe
        if not route.driver:
            issues.append("Chưa gán tài xế")
        
        if not route.vehicle:
            issues.append("Chưa gán xe")
        elif not route.vehicle.can_operate():
            issues.append("Xe không thể hoạt động")
        
        # 4. Kiểm tra điểm dừng
        stops = route.stops.filter(is_active=True)
        if stops.count() == 0:
            issues.append("Chưa có điểm dừng")
        elif stops.count() > 20:
            warnings.append(f"Quá nhiều điểm dừng: {stops.count()}")
        
        return {
            'is_feasible': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics,
            'utilization': round((student_count / route.vehicle.capacity * 100), 1) if route.vehicle else 0
        }


class ETAService:
    """✅ Cải thiện dự đoán ETA"""
    
    @staticmethod
    def calculate_eta(trip, stop, traffic_factor=1.0):
        """
        Tính ETA với nhiều yếu tố
        
        Args:
            trip: Trip object
            stop: RouteStop object
            traffic_factor: Hệ số giao thông (1.0 = bình thường, 1.5 = tắc)
        
        Returns:
            datetime: Thời gian đến dự kiến
        """
        from apps.tracking.models import LocationLog, StopArrival
        
        # Lấy vị trí hiện tại
        latest_log = trip.location_logs.order_by('-timestamp').first()
        
        if not latest_log:
            # Chưa có dữ liệu GPS, dùng scheduled time
            return timezone.datetime.combine(
                trip.trip_date,
                stop.estimated_arrival or timezone.now().time()
            )
        
        # Tính khoảng cách còn lại
        distance_remaining = RouteOptimizationService.haversine_distance(
            latest_log.location,
            stop.location
        )
        
        # Tính tốc độ trung bình từ lịch sử
        recent_logs = trip.location_logs.order_by('-timestamp')[:10]
        avg_speed = sum(float(log.speed or 0) for log in recent_logs) / len(recent_logs)
        
        if avg_speed < 5:  # Xe đang dừng
            avg_speed = 20  # Giả định tốc độ sau khi khởi động
        
        # Áp dụng traffic factor
        effective_speed = avg_speed / traffic_factor
        
        # Tính thời gian di chuyển
        travel_time_hours = distance_remaining / effective_speed if effective_speed > 0 else 0
        travel_time_minutes = travel_time_hours * 60
        
        # Thêm thời gian dừng tại các điểm trước đó
        completed_stops = StopArrival.objects.filter(
            trip=trip,
            actual_arrival__isnull=False
        ).values_list('stop_id', flat=True)
        
        remaining_stops = trip.route.stops.filter(
            stop_order__lt=stop.stop_order,
            is_active=True
        ).exclude(id__in=completed_stops)
        
        stop_time = sum(s.stop_duration or 2 for s in remaining_stops)
        
        # Tổng thời gian
        total_minutes = travel_time_minutes + stop_time
        
        # Tính ETA
        eta = timezone.now() + timedelta(minutes=total_minutes)
        
        # Lưu vào database
        from apps.tracking.models import ETARecord
        ETARecord.objects.create(
            trip=trip,
            stop=stop,
            estimated_arrival=eta,
            distance_remaining=distance_remaining,
            estimated_time_minutes=int(total_minutes)
        )
        
        return eta
    
    @staticmethod
    def get_traffic_factor():
        """
        ✅ Tính hệ số giao thông dựa trên giờ
        
        Returns:
            float: Traffic factor (1.0 - 2.0)
        """
        now = timezone.localtime()
        hour = now.hour
        
        # Giờ cao điểm sáng (7-9h)
        if 7 <= hour < 9:
            return 1.5
        
        # Giờ cao điểm chiều (16-18h)
        elif 16 <= hour < 18:
            return 1.7
        
        # Giờ thấp điểm
        elif 10 <= hour < 15:
            return 0.9
        
        # Bình thường
        else:
            return 1.0