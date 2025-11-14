from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an admin
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsDriver(permissions.BasePermission):
    """
    Permission class to check if user is a driver
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'driver'


class IsParent(permissions.BasePermission):
    """
    Permission class to check if user is a parent
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'parent'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class to check if user is owner of object or admin
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object has parent attribute
        if hasattr(obj, 'parent'):
            return obj.parent.user == request.user
        
        # Check if object has driver attribute
        if hasattr(obj, 'driver'):
            return obj.driver.user == request.user
        
        return False


class IsDriverOfTrip(permissions.BasePermission):
    """
    Permission class to check if user is the driver of the trip
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'driver'):
            return obj.driver.user == request.user
        
        if hasattr(obj, 'trip') and hasattr(obj.trip, 'driver'):
            return obj.trip.driver.user == request.user
        
        return False


class IsParentOfStudent(permissions.BasePermission):
    """
    Permission class to check if user is parent of the student
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'parent'):
            return obj.parent.user == request.user
        
        if hasattr(obj, 'student') and hasattr(obj.student, 'parent'):
            return obj.student.parent.user == request.user
        
        return False


class CanViewTrip(permissions.BasePermission):
    """
    Permission for viewing trips - Admin, Driver, or Parent of students on the trip
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin can view all
        if user.role == 'admin':
            return True
        
        # Driver can view their own trips
        if user.role == 'driver' and hasattr(user, 'driver_profile'):
            return obj.driver == user.driver_profile
        
        # Parent can view trips where their children are assigned
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            from apps.routes.models import StudentRoute
            student_ids = user.parent_profile.students.filter(is_active=True).values_list('id', flat=True)
            route_assignments = StudentRoute.objects.filter(
                student_id__in=student_ids,
                route=obj.route,
                is_active=True
            )
            return route_assignments.exists()
        
        return False


class CanManageRoute(permissions.BasePermission):
    """
    Permission for managing routes - Admin only
    """
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return request.user.is_authenticated
        return request.user.role == 'admin'


class CanTakeAttendance(permissions.BasePermission):
    """
    Permission for taking attendance - Admin or assigned driver
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'driver']
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'driver' and hasattr(request.user, 'driver_profile'):
            if hasattr(obj, 'trip'):
                return obj.trip.driver == request.user.driver_profile
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Read-only permission for any authenticated user
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in permissions.SAFE_METHODS