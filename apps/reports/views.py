from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg
from .models import DailyReport
from .serializers import DailyReportSerializer
from apps.tracking.models import Trip
from apps.authentication.models import User
from utils.permissions import IsAdmin

class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyReport.objects.all()
    serializer_class = DailyReportSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Thống kê tổng quan cho Dashboard"""
        today = timezone.now().date()
        
        data = {
            'total_users': User.objects.count(),
            'total_trips_today': Trip.objects.filter(trip_date=today).count(),
            'trips_active': Trip.objects.filter(status='in_progress').count(),
            'trips_completed': Trip.objects.filter(trip_date=today, status='completed').count(),
            'trips_cancelled': Trip.objects.filter(trip_date=today, status='cancelled').count(),
        }
        return Response(data)