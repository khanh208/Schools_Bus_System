from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta, datetime

from .models import (
    Trip, LocationLog, StopArrival, TripIssue, ETARecord
)
from .serializers import (
    TripListSerializer, TripDetailSerializer, TripCreateSerializer,
    LocationLogSerializer, LocationLogCreateSerializer,
    StopArrivalSerializer, TripIssueSerializer, ETARecordSerializer,
    TripTrackingSerializer
)
from utils.permissions import IsAdmin, IsDriver, CanViewTrip
from utils.pagination import StandardResultsSetPagination


class TripViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trips"""
    queryset = Trip.objects.select_related(
        'route', 'driver', 'vehicle'
    ).all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['trip_date', 'trip_type', 'status', 'route', 'driver']
    ordering_fields = ['trip_date', 'scheduled_start_time', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TripListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TripCreateSerializer
        return TripDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        elif self.action == 'retrieve':
            return [IsAuthenticated(), CanViewTrip()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Drivers see their own trips
        if user.role == 'driver' and hasattr(user, 'driver_profile'):
            queryset = queryset.filter(driver=user.driver_profile)
        
        # Parents see trips for their children's routes
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            from apps.routes.models import StudentRoute
            student_ids = user.parent_profile.students.filter(is_active=True).values_list('id', flat=True)
            route_ids = StudentRoute.objects.filter(
                student_id__in=student_ids,
                is_active=True
            ).values_list('route_id', flat=True)
            queryset = queryset.filter(route_id__in=route_ids)
        
        # Filter by date
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(trip_date=date_param)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def start(self, request, pk=None):
        """Start a trip"""
        trip = self.get_object()
        
        # Check if driver is authorized
        if hasattr(request.user, 'driver_profile'):
            if trip.driver != request.user.driver_profile:
                return Response({
                    'error': 'You are not assigned to this trip'
                }, status=status.HTTP_403_FORBIDDEN)
        
        if trip.start_trip():
            return Response({
                'message': 'Trip started successfully',
                'trip': TripDetailSerializer(trip).data
            })
        
        return Response({
            'error': 'Trip cannot be started'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def complete(self, request, pk=None):
        """Complete a trip"""
        trip = self.get_object()
        
        if hasattr(request.user, 'driver_profile'):
            if trip.driver != request.user.driver_profile:
                return Response({
                    'error': 'You are not assigned to this trip'
                }, status=status.HTTP_403_FORBIDDEN)
        
        if trip.complete_trip():
            return Response({
                'message': 'Trip completed successfully',
                'trip': TripDetailSerializer(trip).data
            })
        
        return Response({
            'error': 'Trip cannot be completed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def cancel(self, request, pk=None):
        """Cancel a trip"""
        trip = self.get_object()
        reason = request.data.get('reason', '')
        
        if trip.cancel_trip(reason):
            return Response({
                'message': 'Trip cancelled successfully'
            })
        
        return Response({
            'error': 'Trip cannot be cancelled'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Get real-time tracking data for trip"""
        trip = self.get_object()
        
        if trip.status != 'in_progress':
            return Response({
                'error': 'Trip is not in progress'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current location
        current_log = trip.location_logs.order_by('-timestamp').first()
        current_location = None
        if current_log:
            current_location = {
                'lat': current_log.location.y,
                'lng': current_log.location.x,
                'speed': float(current_log.speed) if current_log.speed else 0,
                'timestamp': current_log.timestamp
            }
        
        # Get next stop
        from apps.tracking.models import StopArrival
        completed_stops = StopArrival.objects.filter(
            trip=trip,
            actual_arrival__isnull=False
        ).values_list('stop_id', flat=True)
        
        next_stop = trip.route.stops.filter(
            is_active=True
        ).exclude(id__in=completed_stops).order_by('stop_order').first()
        
        next_stop_data = None
        eta_minutes = None
        distance_to_next = None
        
        if next_stop and current_log:
            from apps.routes.services import RouteOptimizationService, ETAService
            
            distance_to_next = RouteOptimizationService.calculate_distance(
                current_log.location, next_stop.location
            )
            
            eta = ETAService.calculate_eta(trip, next_stop)
            if eta:
                eta_minutes = (eta - timezone.now()).total_seconds() / 60
            
            next_stop_data = {
                'id': next_stop.id,
                'name': next_stop.stop_name,
                'order': next_stop.stop_order,
                'lat': next_stop.location.y,
                'lng': next_stop.location.x,
                'scheduled_arrival': next_stop.estimated_arrival
            }
        
        # Calculate progress
        total_stops = trip.route.stops.filter(is_active=True).count()
        completed_stop_count = len(completed_stops)
        progress_percentage = (completed_stop_count / total_stops * 100) if total_stops > 0 else 0
        
        # Get recent locations for path
        recent_locations = trip.location_logs.order_by('-timestamp')[:20]
        
        return Response({
            'trip': TripDetailSerializer(trip).data,
            'current_location': current_location,
            'next_stop': next_stop_data,
            'eta_minutes': round(eta_minutes) if eta_minutes else None,
            'distance_to_next_stop': round(distance_to_next, 2) if distance_to_next else None,
            'progress_percentage': round(progress_percentage, 1),
            'recent_locations': LocationLogSerializer(recent_locations, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's trips"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(trip_date=today)
        serializer = TripListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active trips"""
        queryset = self.get_queryset().filter(status='in_progress')
        serializer = TripListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get trip performance metrics"""
        trip = self.get_object()
        
        if not hasattr(trip, 'performance'):
            return Response({
                'error': 'Performance data not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        from apps.reports.serializers import TripPerformanceSerializer
        serializer = TripPerformanceSerializer(trip.performance)
        return Response(serializer.data)


class LocationLogViewSet(viewsets.ModelViewSet):
    """ViewSet for GPS location logs"""
    queryset = LocationLog.objects.select_related('trip', 'driver').all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['trip', 'driver']
    ordering_fields = ['timestamp']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LocationLogCreateSerializer
        return LocationLogSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsDriver()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def bulk_create(self, request):
        """Bulk create location logs"""
        logs_data = request.data.get('logs', [])
        
        created_logs = []
        errors = []
        
        for log_data in logs_data:
            serializer = LocationLogCreateSerializer(data=log_data)
            if serializer.is_valid():
                log = serializer.save()
                created_logs.append(LocationLogSerializer(log).data)
            else:
                errors.append({
                    'data': log_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created': len(created_logs),
            'logs': created_logs,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_logs else status.HTTP_400_BAD_REQUEST)


class StopArrivalViewSet(viewsets.ModelViewSet):
    """ViewSet for stop arrivals"""
    queryset = StopArrival.objects.select_related('trip', 'stop').all()
    serializer_class = StopArrivalSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['trip', 'stop']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDriver()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def record_arrival(self, request):
        """Record arrival at a stop"""
        from django.contrib.gis.geos import Point
        
        trip_id = request.data.get('trip_id')
        stop_id = request.data.get('stop_id')
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not all([trip_id, stop_id]):
            return Response({
                'error': 'trip_id and stop_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.tracking.models import Trip
            from apps.routes.models import RouteStop
            
            trip = Trip.objects.get(id=trip_id)
            stop = RouteStop.objects.get(id=stop_id)
        except (Trip.DoesNotExist, RouteStop.DoesNotExist):
            return Response({
                'error': 'Trip or stop not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        location = Point(float(lng), float(lat)) if lat and lng else None
        
        arrival, created = StopArrival.objects.update_or_create(
            trip=trip,
            stop=stop,
            defaults={
                'actual_arrival': timezone.now(),
                'location': location
            }
        )
        
        serializer = StopArrivalSerializer(arrival)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TripIssueViewSet(viewsets.ModelViewSet):
    """ViewSet for trip issues"""
    queryset = TripIssue.objects.select_related('trip', 'reported_by').all()
    serializer_class = TripIssueSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['trip', 'issue_type', 'severity', 'is_resolved']
    ordering_fields = ['created_at', 'severity']
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def resolve(self, request, pk=None):
        """Resolve an issue"""
        issue = self.get_object()
        
        issue.is_resolved = True
        issue.resolved_at = timezone.now()
        issue.resolution_notes = request.data.get('notes', '')
        issue.save()
        
        return Response({
            'message': 'Issue resolved successfully'
        })
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get unresolved issues"""
        queryset = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)