# utils/permissions.py
from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Chỉ cho phép Admin truy cập"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'admin'

class IsDriver(permissions.BasePermission):
    """Chỉ cho phép Tài xế truy cập"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'driver'

class IsParent(permissions.BasePermission):
    """Chỉ cho phép Phụ huynh truy cập"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'parent'

class CanManageRoute(permissions.BasePermission):
    """Quyền quản lý tuyến đường (Admin)"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'admin'

class CanViewTrip(permissions.BasePermission):
    """Quyền xem chuyến đi"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, 'role', '') == 'admin': return True
        if getattr(user, 'role', '') == 'driver': return obj.driver.user == user
        if getattr(user, 'role', '') == 'parent': return True 
        return False

class CanTakeAttendance(permissions.BasePermission):
    """Quyền điểm danh (Tài xế)"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', '') in ['driver', 'admin']

class IsParentOfStudent(permissions.BasePermission):
    """Chỉ phụ huynh của học sinh mới được xem"""
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'role', '') == 'admin': return True
        if getattr(request.user, 'role', '') == 'parent':
            return obj.parent.user == request.user
        return False

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Chỉ cho phép chủ sở hữu (người tạo/upload) hoặc Admin được thao tác.
    """
    def has_object_permission(self, request, view, obj):
        # Admin luôn được phép
        if getattr(request.user, 'role', '') == 'admin':
            return True
            
        # Kiểm tra quyền sở hữu dựa trên các trường phổ biến
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
            
        return False