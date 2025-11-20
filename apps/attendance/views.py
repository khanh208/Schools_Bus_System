# apps/attendance/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from datetime import timedelta

from .models import Attendance
from .serializers import (
    AttendanceSerializer,
    AttendanceCheckInSerializer,
    BulkAttendanceSerializer,
)
from utils.permissions import IsAdmin, IsDriver, CanTakeAttendance
from utils.pagination import StandardResultsSetPagination


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý điểm danh"""
    queryset = Attendance.objects.select_related(
        'trip', 'student', 'stop', 'checked_by'
    ).all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['trip', 'student', 'attendance_type', 'status']
    ordering_fields = ['check_time', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Phụ huynh chỉ xem được điểm danh của con mình
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)

        # Tài xế chỉ xem được điểm danh trong các trip của mình
        elif user.role == 'driver' and hasattr(user, 'driver_profile'):
            queryset = queryset.filter(trip__driver=user.driver_profile)

        # Lọc theo khoảng ngày
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if from_date:
            queryset = queryset.filter(check_time__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_time__date__lte=to_date)

        return queryset

    @action(detail=False, methods=['post'], permission_classes=[CanTakeAttendance])
    def check_in(self, request):
        """Điểm danh 1 học sinh"""
        serializer = AttendanceCheckInSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            attendance = serializer.save()
            return Response(
                AttendanceSerializer(attendance).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[CanTakeAttendance])
    def bulk_check_in(self, request):
        """Điểm danh hàng loạt"""
        serializer = BulkAttendanceSerializer(data=request.data)

        if serializer.is_valid():
            trip_id = serializer.validated_data['trip_id']
            records = serializer.validated_data['attendance_records']

            from apps.tracking.models import Trip
            try:
                trip = Trip.objects.get(id=trip_id)
            except Trip.DoesNotExist:
                return Response({
                    'error': 'Trip not found'
                }, status=status.HTTP_404_NOT_FOUND)

            created_records = []
            errors = []

            for record in records:
                try:
                    attendance = Attendance.objects.create(
                        trip=trip,
                        student_id=record['student_id'],
                        attendance_type='check_in',
                        status=record['status'],
                        check_time=timezone.now(),
                        checked_by=request.user,
                        notes=record.get('notes', '')
                    )
                    attendance.send_notification_to_parent()
                    created_records.append(AttendanceSerializer(attendance).data)
                except Exception as e:
                    errors.append({
                        'student_id': record['student_id'],
                        'error': str(e)
                    })

            return Response({
                'created': len(created_records),
                'records': created_records,
                'errors': errors
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Lấy điểm danh hôm nay"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(check_time__date=today)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Thống kê điểm danh trong khoảng ngày"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        if not from_date or not to_date:
            return Response({
                'error': 'from_date and to_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            check_time__date__gte=from_date,
            check_time__date__lte=to_date,
            attendance_type='check_in'
        )

        stats = {
            'total': queryset.count(),
            'present': queryset.filter(status='present').count(),
            'absent': queryset.filter(status='absent').count(),
            'late': queryset.filter(status='late').count(),
        }

        stats['attendance_rate'] = (
            (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
        )

        return Response(stats)
