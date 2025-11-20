from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from apps.students.models import Student
from apps.tracking.models import Trip
from apps.attendance.models import Attendance
from apps.routes.models import Route, Vehicle


@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard"""
    today = timezone.now().date()
    
    # Statistics
    stats = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'total_routes': Route.objects.filter(is_active=True).count(),
        'total_vehicles': Vehicle.objects.filter(is_active=True).count(),
        'today_trips': Trip.objects.filter(trip_date=today).count(),
        'active_trips': Trip.objects.filter(
            trip_date=today,
            status='in_progress'
        ).count(),
        'completed_trips': Trip.objects.filter(
            trip_date=today,
            status='completed'
        ).count(),
    }
    
    # Today's attendance
    today_attendance = Attendance.objects.filter(
        trip__trip_date=today,
        attendance_type='check_in'
    ).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent'))
    )
    
    stats['today_attendance'] = today_attendance
    
    # Recent trips
    recent_trips = Trip.objects.select_related(
        'route', 'driver__user', 'vehicle'
    ).filter(trip_date=today).order_by('-scheduled_start_time')[:10]
    
    context = {
        'title': 'Dashboard',
        'stats': stats,
        'recent_trips': recent_trips,
    }
    
    return render(request, 'admin/dashboard.html', context)