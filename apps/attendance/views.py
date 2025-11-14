from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from .models import (
    Attendance, AttendanceException, AttendanceReport, AttendanceAlert
)
from .serializers import (
    AttendanceSerializer, AttendanceCheckInSerializer, BulkAttendanceSerializer,
    AttendanceExceptionSerializer, AttendanceReportSerializer,
    AttendanceAlertSerializer, AttendanceStatsSerializer
)
from utils.permissions import IsAdmin, IsDriver, CanTakeAttendance
from utils.pagination import StandardResultsSetPagination


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance records"""
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
        
        # Parents can only see their children's attendance
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        # Drivers can only see their trips' attendance
        elif user.role == 'driver' and hasattr(user, 'driver_profile'):
            queryset = queryset.filter(trip__driver=user.driver_profile)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        if from_date:
            queryset = queryset.filter(check_time__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_time__date__lte=to_date)
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[CanTakeAttendance])
    def check_in(self, request):
        """Check in a student"""
        serializer = AttendanceCheckInSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[CanTakeAttendance])
    def bulk_check_in(self, request):
        """Bulk check-in multiple students"""
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
        """Get today's attendance records"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(check_time__date=today)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get attendance statistics"""
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
            'excused': queryset.filter(status='excused').count(),
        }
        
        stats['attendance_rate'] = (
            (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
        )
        
        return Response(stats)


class AttendanceExceptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance exceptions"""
    queryset = AttendanceException.objects.select_related(
        'student', 'approved_by', 'created_by'
    ).all()
    serializer_class = AttendanceExceptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'exception_type', 'is_approved']
    ordering_fields = ['start_date', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see their children's exceptions
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def approve(self, request, pk=None):
        """Approve an exception"""
        exception = self.get_object()
        exception.is_approved = True
        exception.approved_by = request.user
        exception.save()
        
        return Response({
            'message': 'Exception approved successfully'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def reject(self, request, pk=None):
        """Reject an exception"""
        exception = self.get_object()
        exception.is_approved = False
        exception.save()
        
        return Response({
            'message': 'Exception rejected'
        })


class AttendanceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for attendance reports"""
    queryset = AttendanceReport.objects.select_related('student').all()
    serializer_class = AttendanceReportSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'report_type']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see their children's reports
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def generate(self, request):
        """Generate attendance report"""
        from apps.students.models import Student
        
        student_id = request.data.get('student_id')
        report_type = request.data.get('report_type', 'monthly')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not all([student_id, start_date, end_date]):
            return Response({
                'error': 'student_id, start_date, and end_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        report = AttendanceReport.generate_report(
            student, report_type, start_date, end_date
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)


class AttendanceAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance alerts"""
    queryset = AttendanceAlert.objects.select_related(
        'student', 'resolved_by'
    ).all()
    serializer_class = AttendanceAlertSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'alert_type', 'severity', 'is_resolved']
    ordering_fields = ['created_at', 'severity']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see their children's alerts
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.resolution_notes = request.data.get('notes', '')
        alert.save()
        
        return Response({
            'message': 'Alert resolved successfully'
        })
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get unresolved alerts"""
        queryset = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)