# apps/tracking/parent_views.py
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from .models import Trip
from .serializers import TripListSerializer


class ParentTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API để phụ huynh xem danh sách chuyến đi liên quan đến con của mình.
    - GET /api/tracking/parent/trips/      -> list các trip hôm nay
    - Có thể thêm filter sau nếu cần.
    """
    serializer_class = TripListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Nếu không phải phụ huynh thì không cho xem
        if not hasattr(user, 'parent_profile'):
            return Trip.objects.none()

        # Lấy danh sách học sinh của phụ huynh
        parent_profile = user.parent_profile
        student_ids = parent_profile.students.filter(
            is_active=True
        ).values_list('id', flat=True)

        # Lấy các route mà học sinh đang gán
        from apps.routes.models import StudentRoute
        route_ids = StudentRoute.objects.filter(
            student_id__in=student_ids,
            is_active=True,
        ).values_list('route_id', flat=True)

        today = timezone.now().date()

        # Các trip hôm nay của các tuyến đó
        queryset = Trip.objects.select_related(
            'route', 'driver', 'vehicle'
        ).filter(
            route_id__in=route_ids,
            trip_date=today,
        )

        trip_status = self.request.query_params.get('status')
        if trip_status:
            queryset = queryset.filter(status=trip_status)

        return queryset


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def parent_tracking_page(request):
    """
    Trang demo đơn giản cho phụ huynh (tạm trả text).
    Nếu sau này bạn có frontend riêng thì có thể redirect qua đó.
    """
    return HttpResponse(
        "<h1>Parent Tracking</h1>"
        "<p>Đây là trang demo cho phụ huynh theo dõi xe real-time."
        " Hãy dùng mobile/web app để xem bản đồ realtime.</p>",
        content_type="text/html",
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def parent_tracking_demo(request):
    """
    Endpoint demo JSON cho phụ huynh:
    - Dùng để test nhanh API (như link ở script start: /api/tracking/parent/demo/)
    """
    sample = {
        "message": "Parent tracking demo",
        "note": "Hãy login bằng tài khoản phụ huynh rồi gọi /api/tracking/parent/trips/ để lấy danh sách chuyến hôm nay.",
        "example_endpoints": {
            "parent_trips": "/api/tracking/parent/trips/",
            "today_trips": "/api/tracking/trips/today/",
            "active_trips": "/api/tracking/trips/active/",
        },
    }
    return Response(sample)
