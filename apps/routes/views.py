from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q, Count

from .models import (
    Vehicle, Route, RouteStop, StudentRoute, 
    RouteSchedule, VehicleMaintenance
)
from .serializers import (
    VehicleSerializer, VehicleMaintenanceSerializer,
    RouteListSerializer, RouteDetailSerializer, RouteCreateUpdateSerializer,
    RouteStopSerializer, RouteStopCreateSerializer,
    StudentRouteSerializer, RouteScheduleSerializer,
    RouteOptimizationSerializer
)
from utils.permissions import IsAdmin, CanManageRoute
from utils.pagination import StandardResultsSetPagination


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing vehicles"""
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'vehicle_type', 'is_active']
    search_fields = ['plate_number', 'model']
    ordering_fields = ['plate_number', 'capacity', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available vehicles"""
        vehicles = self.get_queryset().filter(
            status='active',
            is_active=True
        )
        serializer = self.get_serializer(vehicles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """Get vehicle maintenance history"""
        vehicle = self.get_object()
        maintenance_records = vehicle.maintenance_records.all()
        serializer = VehicleMaintenanceSerializer(maintenance_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def schedule_maintenance(self, request, pk=None):
        """Schedule vehicle maintenance"""
        vehicle = self.get_object()
        
        serializer = VehicleMaintenanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                vehicle=vehicle,
                created_by=request.user
            )
            
            # Update vehicle status
            vehicle.status = 'maintenance'
            vehicle.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RouteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing routes"""
    queryset = Route.objects.select_related(
        'area', 'vehicle', 'driver'
    ).all()
    # We rely on get_permissions for finer control, so base permission is IsAuthenticated
    permission_classes = [IsAuthenticated] 
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['route_type', 'area', 'is_active']
    search_fields = ['route_code', 'route_name']
    ordering_fields = ['route_code', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RouteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RouteCreateUpdateSerializer
        return RouteDetailSerializer
    
    def get_permissions(self):
        # Admin can create, update, delete, and optimize
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'optimize']:
            return [IsAuthenticated(), IsAdmin()]
        # Others (Driver, Parent) can view
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Drivers can only see their assigned routes
        if user.role == 'driver' and hasattr(user, 'driver_profile'):
            queryset = queryset.filter(driver=user.driver_profile)
        
        # Parents can see routes they're interested in (related to their children)
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            assigned_route_ids = StudentRoute.objects.filter(
                student_id__in=student_ids,
                is_active=True
            ).values_list('route_id', flat=True)
            
            # Allow seeing assigned routes OR active routes they might want to find
            # Ideally, for "finding", we use a separate endpoint, but list view could be broad.
            # For security, let's keep it broad for parents to see available routes? 
            # Or stick to assigned. The requirement usually implies seeing assigned.
            # The 'find_suitable' endpoint handles searching for new ones.
            queryset = queryset.filter(
                Q(id__in=assigned_route_ids) | Q(is_active=True)
            ).distinct()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def stops(self, request, pk=None):
        """Get route stops in order"""
        route = self.get_object()
        stops = route.get_ordered_stops()
        serializer = RouteStopSerializer(stops, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get students assigned to route"""
        route = self.get_object()
        assignments = route.student_assignments.filter(
            is_active=True
        ).select_related('student', 'stop')
        serializer = StudentRouteSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        """Get route schedules"""
        route = self.get_object()
        schedules = route.schedules.filter(is_active=True)
        serializer = RouteScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def optimize(self, request, pk=None):
        """Optimize route stops order"""
        route = self.get_object()
        
        serializer = RouteOptimizationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Import optimization service
        from .services import RouteOptimizationService
        
        try:
            optimized_route = RouteOptimizationService.optimize_route(
                route,
                optimize_by=serializer.validated_data['optimize_by'],
                consider_traffic=serializer.validated_data['consider_traffic']
            )
            
            return Response({
                'message': 'Route optimized successfully',
                'route': RouteDetailSerializer(optimized_route).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def find_suitable(self, request):
        """Find suitable routes for parent based on location"""
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        max_distance = request.data.get('max_distance', 2)  # km
        
        if not lat or not lng:
            return Response({
                'error': 'lat and lng are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            point = Point(float(lng), float(lat))
        except ValueError:
            return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find routes with stops near the location
        from django.contrib.gis.db.models.functions import Distance
        
        nearby_stops = RouteStop.objects.filter(
            is_active=True,
            location__distance_lte=(point, D(km=max_distance))
        ).select_related('route').annotate(
            distance=Distance('location', point)
        ).order_by('distance')[:10]
        
        route_ids = [stop.route_id for stop in nearby_stops]
        routes = Route.objects.filter(
            id__in=route_ids,
            is_active=True
        ).distinct()
        
        serializer = RouteListSerializer(routes, many=True)
        return Response({
            'routes': serializer.data,
            'nearby_stops': [
                {
                    'stop_id': stop.id,
                    'route_id': stop.route_id,
                    'route_code': stop.route.route_code,
                    'stop_name': stop.stop_name,
                    'distance_km': round(stop.distance.km, 2)
                }
                for stop in nearby_stops
            ]
        })


class RouteStopViewSet(viewsets.ModelViewSet):
    """ViewSet for managing route stops"""
    queryset = RouteStop.objects.select_related('route').all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['route', 'is_active']
    ordering_fields = ['stop_order']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RouteStopCreateSerializer
        return RouteStopSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get students assigned to this stop"""
        stop = self.get_object()
        assignments = stop.student_assignments.filter(
            is_active=True
        ).select_related('student')
        serializer = StudentRouteSerializer(assignments, many=True)
        return Response(serializer.data)


class StudentRouteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student route assignments"""
    queryset = StudentRoute.objects.select_related(
        'student', 'route', 'stop'
    ).all()
    serializer_class = StudentRouteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'route', 'assignment_type', 'is_active']
    ordering_fields = ['start_date', 'created_at']
    
    def get_permissions(self):
        # Allow authenticated users (Parents) to create new assignments
        if self.action == 'create':
            return [IsAuthenticated()]
        
        # Only Admins can update/delete assignments to prevent unauthorized changes
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
            
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see their children's assignments
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        # Drivers can see assignments for their routes
        elif user.role == 'driver' and hasattr(user, 'driver_profile'):
            route_ids = Route.objects.filter(
                driver=user.driver_profile
            ).values_list('id', flat=True)
            queryset = queryset.filter(route_id__in=route_ids)
        
        return queryset

    def perform_create(self, serializer):
        """
        Automatically deactivate existing active assignments for this student 
        before creating a new one to ensure only one active route exists.
        """
        student = serializer.validated_data['student']
        
        # Deactivate all currently active assignments for this student
        StudentRoute.objects.filter(
            student=student, 
            is_active=True
        ).update(is_active=False)
        
        # Save the new assignment
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def deactivate(self, request, pk=None):
        """Deactivate a student route assignment"""
        assignment = self.get_object()
        assignment.is_active = False
        assignment.save()
        
        return Response({
            'message': 'Assignment deactivated successfully'
        })


class RouteScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing route schedules"""
    queryset = RouteSchedule.objects.select_related('route').all()
    serializer_class = RouteScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['route', 'day_of_week', 'is_active']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]