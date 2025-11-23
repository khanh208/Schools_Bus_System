"""
Services for route optimization and management
"""

from django.contrib.gis.geos import Point, LineString
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.utils import timezone
from datetime import timedelta
import math


class RouteOptimizationService:
    """Service for optimizing route stops"""
    
    @staticmethod
    def calculate_distance(point1, point2):
        """
        Calculate distance between two points in kilometers
        Args:
            point1: Point object or tuple (lng, lat)
            point2: Point object or tuple (lng, lat)
        Returns:
            float: Distance in kilometers
        """
        if isinstance(point1, tuple):
            point1 = Point(point1[0], point1[1])
        if isinstance(point2, tuple):
            point2 = Point(point2[0], point2[1])
        
        # Using Haversine formula (more accurate for long distances)
        lat1, lon1 = point1.y, point1.x
        lat2, lon2 = point2.y, point2.x
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        
        return c * r
    
    @staticmethod
    def optimize_stops_order(route, start_point=None):
        """
        Optimize the order of stops using nearest neighbor algorithm
        Args:
            route: Route object
            start_point: Starting point (school location)
        Returns:
            list: Optimized list of stops
        """
        from apps.routes.models import RouteStop
        
        stops = list(route.stops.filter(is_active=True))
        if not stops:
            return []
        
        # If no start point provided, use first stop
        if start_point is None:
            start_point = stops[0].location
        
        optimized = []
        remaining = stops.copy()
        current_point = start_point
        
        # Nearest neighbor algorithm
        while remaining:
            nearest_stop = min(
                remaining,
                key=lambda s: RouteOptimizationService.calculate_distance(
                    current_point, s.location
                )
            )
            optimized.append(nearest_stop)
            remaining.remove(nearest_stop)
            current_point = nearest_stop.location
        
        # Update stop orders
        for idx, stop in enumerate(optimized, start=1):
            stop.stop_order = idx
            stop.save(update_fields=['stop_order'])
        
        return optimized
    
    @staticmethod
    def calculate_route_duration(route):
        """
        Calculate estimated duration for a route
        Args:
            route: Route object
        Returns:
            int: Duration in minutes
        """
        stops = route.stops.filter(is_active=True).order_by('stop_order')
        
        if stops.count() < 2:
            return 0
        
        total_duration = 0
        avg_speed = 30  # km/h average speed in city
        
        # Calculate travel time between stops
        for i in range(len(stops) - 1):
            distance = RouteOptimizationService.calculate_distance(
                stops[i].location,
                stops[i + 1].location
            )
            travel_time = (distance / avg_speed) * 60  # Convert to minutes
            stop_time = stops[i].stop_duration or 2  # Default 2 minutes per stop
            
            total_duration += travel_time + stop_time
        
        return int(total_duration)
    
    @staticmethod
    def find_optimal_route(start_point, end_point, waypoints):
        """
        Find optimal route through waypoints
        Args:
            start_point: Starting Point
            end_point: Ending Point
            waypoints: List of Point objects
        Returns:
            list: Ordered list of points
        """
        if not waypoints:
            return [start_point, end_point]
        
        # Simple nearest neighbor from start to end
        ordered_points = [start_point]
        remaining = waypoints.copy()
        current = start_point
        
        while remaining:
            nearest = min(
                remaining,
                key=lambda p: RouteOptimizationService.calculate_distance(current, p)
            )
            ordered_points.append(nearest)
            remaining.remove(nearest)
            current = nearest
        
        ordered_points.append(end_point)
        return ordered_points
    
    @staticmethod
    def check_route_capacity(route):
        """
        Check if vehicle has enough capacity for assigned students
        Args:
            route: Route object
        Returns:
            dict: Capacity check results
        """
        from apps.routes.models import StudentRoute
        
        vehicle = route.vehicle
        if not vehicle:
            return {
                'valid': False,
                'message': 'No vehicle assigned',
                'capacity': 0,
                'assigned': 0
            }
        
        assigned_students = StudentRoute.objects.filter(
            route=route,
            is_active=True
        ).count()
        
        return {
            'valid': assigned_students <= vehicle.capacity,
            'capacity': vehicle.capacity,
            'assigned': assigned_students,
            'available': vehicle.capacity - assigned_students,
            'message': 'OK' if assigned_students <= vehicle.capacity else 'Over capacity'
        }


class ETAService:
    """Service for calculating Estimated Time of Arrival"""
    
    @staticmethod
    def calculate_eta(trip, stop):
        """
        Calculate ETA for a specific stop
        Args:
            trip: Trip object
            stop: RouteStop object
        Returns:
            datetime: Estimated arrival time
        """
        from apps.tracking.models import LocationLog
        
        # Get latest location
        latest_log = trip.location_logs.order_by('-timestamp').first()
        
        if not latest_log:
            # No location data, return scheduled time
            return timezone.datetime.combine(
                trip.trip_date,
                stop.estimated_arrival or timezone.now().time()
            )
        
        # Calculate distance to stop
        distance = RouteOptimizationService.calculate_distance(
            latest_log.location,
            stop.location
        )
        
        # Get current speed or use average
        current_speed = float(latest_log.speed) if latest_log.speed else 25.0  # km/h
        
        # Adjust speed based on traffic (simple model)
        hour = timezone.now().hour
        if 7 <= hour <= 9 or 16 <= hour <= 18:  # Rush hours
            current_speed *= 0.7  # Reduce speed by 30%
        
        # Calculate time
        if current_speed > 0:
            time_hours = distance / current_speed
            time_minutes = time_hours * 60
        else:
            time_minutes = distance * 3  # Rough estimate: 3 min per km
        
        # Add buffer for stops
        remaining_stops = trip.route.stops.filter(
            stop_order__lt=stop.stop_order,
            is_active=True
        ).count()
        time_minutes += remaining_stops * 2  # 2 minutes per stop
        
        # Calculate ETA
        eta = timezone.now() + timedelta(minutes=time_minutes)
        
        # Save ETA record
        from apps.tracking.models import ETARecord
        ETARecord.objects.create(
            trip=trip,
            stop=stop,
            estimated_arrival=eta,
            distance_remaining=distance,
            estimated_time_minutes=int(time_minutes)
        )
        
        return eta
    
    @staticmethod
    def calculate_all_etas(trip):
        """
        Calculate ETA for all remaining stops
        Args:
            trip: Trip object
        Returns:
            dict: Dictionary of stop_id: eta
        """
        from apps.tracking.models import StopArrival
        
        # Get completed stops
        completed_stop_ids = StopArrival.objects.filter(
            trip=trip,
            actual_arrival__isnull=False
        ).values_list('stop_id', flat=True)
        
        # Get remaining stops
        remaining_stops = trip.route.stops.filter(
            is_active=True
        ).exclude(id__in=completed_stop_ids).order_by('stop_order')
        
        etas = {}
        for stop in remaining_stops:
            eta = ETAService.calculate_eta(trip, stop)
            etas[stop.id] = {
                'stop_id': stop.id,
                'stop_name': stop.stop_name,
                'eta': eta,
                'minutes_away': (eta - timezone.now()).total_seconds() / 60
            }
        
        return etas


class RouteRecommendationService:
    """Service for recommending routes to parents"""
    
    @staticmethod
    def find_nearby_routes(location, max_distance_km=2.0):
        """
        Find routes with stops near a location
        Args:
            location: Point object or tuple (lng, lat)
            max_distance_km: Maximum distance in kilometers
        Returns:
            list: List of (route, stop, distance) tuples
        """
        from apps.routes.models import RouteStop, Route
        
        if isinstance(location, tuple):
            location = Point(location[0], location[1])
        
        # Find nearby stops
        nearby_stops = RouteStop.objects.filter(
            is_active=True,
            location__distance_lte=(location, D(km=max_distance_km))
        ).select_related('route').annotate(
            distance=Distance('location', location)
        ).order_by('distance')
        
        results = []
        seen_routes = set()
        
        for stop in nearby_stops:
            if stop.route_id not in seen_routes:
                route = stop.route
                if route.is_active and route.is_fully_assigned:
                    results.append({
                        'route': route,
                        'nearest_stop': stop,
                        'distance_km': round(stop.distance.km, 2)
                    })
                    seen_routes.add(route.id)
        
        return results
    
    @staticmethod
    def recommend_best_route(pickup_location, dropoff_location, preferences=None):
        """
        Recommend the best route based on locations and preferences
        Args:
            pickup_location: Point object
            dropoff_location: Point object
            preferences: dict with user preferences
        Returns:
            dict: Recommended route info
        """
        if preferences is None:
            preferences = {}
        
        max_distance = preferences.get('max_distance_km', 2.0)
        
        # Find routes near pickup location
        pickup_routes = RouteRecommendationService.find_nearby_routes(
            pickup_location,
            max_distance
        )
        
        if not pickup_routes:
            return None
        
        # Score routes based on multiple factors
        scored_routes = []
        for route_info in pickup_routes:
            route = route_info['route']
            score = 0
            
            # Factor 1: Distance to pickup (40%)
            pickup_distance = route_info['distance_km']
            score += (1 - min(pickup_distance / max_distance, 1)) * 40
            
            # Factor 2: Available capacity (30%)
            capacity_check = RouteOptimizationService.check_route_capacity(route)
            if capacity_check['valid'] and capacity_check['available'] > 0:
                score += (capacity_check['available'] / capacity_check['capacity']) * 30
            
            # Factor 3: Route duration (20%)
            if route.estimated_duration:
                # Prefer shorter routes
                score += max(0, (60 - route.estimated_duration) / 60 * 20)
            
            # Factor 4: Driver rating (10%)
            if route.driver:
                score += (float(route.driver.rating) / 5.0) * 10
            
            scored_routes.append({
                'route': route,
                'stop': route_info['nearest_stop'],
                'distance': pickup_distance,
                'score': score,
                'capacity_info': capacity_check
            })
        
        # Sort by score
        scored_routes.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_routes[0] if scored_routes else None