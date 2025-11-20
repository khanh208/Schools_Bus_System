from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView
from apps.reports.admin_views import admin_dashboard

# API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="School Bus Management API",
        default_version='v1',
        description="API documentation for School Bus Management System",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@schoolbus.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/students/', include('apps.students.urls')),
    path('api/routes/', include('apps.routes.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/tracking/', include('apps.tracking.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/backup/', include('apps.backup.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('admin/dashboard/', admin_dashboard, name='admin-dashboard'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Custom admin site configuration
admin.site.site_header = "School Bus Management"
admin.site.site_title = "School Bus Admin"
admin.site.index_title = "Welcome to School Bus Management System"