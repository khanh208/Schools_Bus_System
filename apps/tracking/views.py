from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Trip, LocationLog, StopArrival
from .serializers import (
    TripListSerializer, TripDetailSerializer, TripCreateSerializer,
    LocationLogSerializer, LocationLogCreateSerializer,
    StopArrivalSerializer, TripTrackingSerializer,
)
from utils.permissions import IsAdmin, IsDriver, CanViewTrip
from utils.pagination import StandardResultsSetPagination


class TripViewSet(viewsets.ModelViewSet):
    """Quản lý chuyến đi"""
    queryset = Trip.objects.select_related('route', 'driver', 'vehicle').all()
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

        # Driver chỉ thấy chuyến của mình
        if getattr(user, 'role', '') == 'driver' and hasattr(user, 'driver_profile'):
            queryset = queryset.filter(driver=user.driver_profile)

        # Phụ huynh thấy chuyến tương ứng tuyến của con
        elif getattr(user, 'role', '') == 'parent' and hasattr(user, 'parent_profile'):
            from apps.routes.models import StudentRoute
            student_ids = user.parent_profile.students.filter(
                is_active=True
            ).values_list('id', flat=True)

            route_ids = StudentRoute.objects.filter(
                student_id__in=student_ids,
                is_active=True,
            ).values_list('route_id', flat=True)

            queryset = queryset.filter(route_id__in=route_ids)

        # filter theo ngày nếu có ?date=YYYY-MM-DD
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(trip_date=date_param)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def start(self, request, pk=None):
        """Bắt đầu chuyến đi"""
        trip = self.get_object()

        if hasattr(request.user, 'driver_profile'):
            if trip.driver != request.user.driver_profile:
                return Response(
                    {'error': 'Bạn không được gán cho chuyến này.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if trip.start_trip():
            return Response(
                {
                    'message': 'Bắt đầu chuyến đi thành công.',
                    'trip': TripDetailSerializer(trip).data,
                }
            )

        return Response(
            {'error': 'Không thể bắt đầu chuyến đi.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def complete(self, request, pk=None):
        """Hoàn thành chuyến đi"""
        trip = self.get_object()

        if hasattr(request.user, 'driver_profile'):
            if trip.driver != request.user.driver_profile:
                return Response(
                    {'error': 'Bạn không được gán cho chuyến này.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if trip.complete_trip():
            return Response(
                {
                    'message': 'Hoàn thành chuyến đi thành công.',
                    'trip': TripDetailSerializer(trip).data,
                }
            )

        return Response(
            {'error': 'Không thể hoàn thành chuyến đi.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def cancel(self, request, pk=None):
        """
        Huỷ chuyến đi (đơn giản: chỉ set status = cancelled)
        """
        trip = self.get_object()
        reason = request.data.get('reason', '')

        # Nếu trong model Trip có method cancel_trip thì dùng,
        # không thì set thẳng status.
        if hasattr(trip, 'cancel_trip'):
            ok = trip.cancel_trip(reason)
        else:
            trip.status = 'cancelled'
            trip.notes = (trip.notes or '') + f'\n[Cancel reason]: {reason}'
            trip.save(update_fields=['status', 'notes'])
            ok = True

        if ok:
            return Response({'message': 'Huỷ chuyến đi thành công.'})
        return Response(
            {'error': 'Không thể huỷ chuyến đi.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """
        API phục vụ màn hình tracking realtime:
        - Vị trí hiện tại
        - Điểm dừng kế tiếp + ETA
        - % tiến độ chuyến
        """
        trip = self.get_object()

        if trip.status != 'in_progress':
            return Response(
                {'error': 'Chuyến đi hiện không ở trạng thái đang chạy.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vị trí hiện tại
        current_log = trip.location_logs.order_by('-timestamp').first()
        current_location = None
        if current_log and current_log.location:
            current_location = {
                'lat': current_log.location.y,
                'lng': current_log.location.x,
                'speed': float(current_log.speed) if current_log.speed else 0.0,
                'timestamp': current_log.timestamp,
            }

        # Các điểm dừng đã hoàn thành
        from apps.tracking.models import StopArrival as StopArrivalModel

        completed_stops = StopArrivalModel.objects.filter(
            trip=trip,
            actual_arrival__isnull=False,
        ).values_list('stop_id', flat=True)

        # Điểm dừng tiếp theo
        next_stop = trip.route.stops.filter(
            is_active=True
        ).exclude(id__in=completed_stops).order_by('stop_order').first()

        next_stop_data = None
        eta_minutes = None
        distance_to_next = None

        if next_stop and current_log and current_log.location:
            from apps.routes.services import RouteOptimizationService, ETAService

            distance_to_next = RouteOptimizationService.calculate_distance(
                current_log.location,
                next_stop.location,
            )

            eta = ETAService.calculate_eta(trip, next_stop)
            if eta:
                eta_minutes = (eta - timezone.now()).total_seconds() / 60.0

            next_stop_data = {
                'id': next_stop.id,
                'name': next_stop.stop_name,
                'order': next_stop.stop_order,
                'lat': next_stop.location.y,
                'lng': next_stop.location.x,
                'scheduled_arrival': getattr(next_stop, 'estimated_arrival', None),
            }

        # Tính % tiến độ
        total_stops = trip.route.stops.filter(is_active=True).count()
        completed_stop_count = len(completed_stops)
        progress_percentage = (completed_stop_count / total_stops * 100) if total_stops > 0 else 0

        # Lịch sử vị trí gần nhất
        recent_locations = trip.location_logs.order_by('-timestamp')[:20]

        data = {
            'trip': TripDetailSerializer(trip).data,
            'current_location': current_location,
            'next_stop': next_stop_data,
            'eta_minutes': round(eta_minutes) if eta_minutes is not None else None,
            'distance_to_next_stop': round(distance_to_next, 2) if distance_to_next is not None else None,
            'progress_percentage': round(progress_percentage, 1),
            'recent_locations': LocationLogSerializer(recent_locations, many=True).data,
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Danh sách chuyến của hôm nay"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(trip_date=today)
        serializer = TripListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Danh sách chuyến đang chạy"""
        queryset = self.get_queryset().filter(status='in_progress')
        serializer = TripListSerializer(queryset, many=True)
        return Response(serializer.data)


class LocationLogViewSet(viewsets.ModelViewSet):
    """Quản lý log GPS"""
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
        if self.action in ['create', 'bulk_create']:
            return [IsAuthenticated(), IsDriver()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def bulk_create(self, request):
        """Driver gửi nhiều điểm GPS 1 lần"""
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
                    'errors': serializer.errors,
                })

        return Response(
            {
                'created': len(created_logs),
                'logs': created_logs,
                'errors': errors,
            },
            status=status.HTTP_201_CREATED if created_logs else status.HTTP_400_BAD_REQUEST,
        )


class StopArrivalViewSet(viewsets.ModelViewSet):
    """Quản lý thời điểm xe đến điểm dừng"""
    queryset = StopArrival.objects.select_related('trip', 'stop').all()
    serializer_class = StopArrivalSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['trip', 'stop']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'record_arrival']:
            return [IsAuthenticated(), IsDriver()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsDriver])
    def record_arrival(self, request):
        """Driver báo là đã đến 1 điểm dừng"""
        from django.contrib.gis.geos import Point
        from apps.routes.models import RouteStop
        from apps.tracking.models import Trip as TripModel

        trip_id = request.data.get('trip_id')
        stop_id = request.data.get('stop_id')
        lat = request.data.get('lat')
        lng = request.data.get('lng')

        if not all([trip_id, stop_id]):
            return Response(
                {'error': 'trip_id và stop_id là bắt buộc.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            trip = TripModel.objects.get(id=trip_id)
            stop = RouteStop.objects.get(id=stop_id)
        except (TripModel.DoesNotExist, RouteStop.DoesNotExist):
            return Response(
                {'error': 'Không tìm thấy chuyến đi hoặc điểm dừng.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        arrival, created = StopArrival.objects.update_or_create(
            trip=trip,
            stop=stop,
            defaults={
                'actual_arrival': timezone.now(),
                # 'location': Point(float(lng), float(lat)) if lat and lng else None, # Uncomment nếu model có field location
            },
        )

        serializer = StopArrivalSerializer(arrival)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )