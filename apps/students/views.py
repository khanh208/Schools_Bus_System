from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count

from .models import (
    Class, Area, Student, StudentNote, 
    StudentDocument, EmergencyContact
)
from .serializers import (
    ClassSerializer, AreaSerializer,
    StudentListSerializer, StudentDetailSerializer,
    StudentCreateUpdateSerializer, StudentNoteSerializer,
    StudentDocumentSerializer, EmergencyContactSerializer
)
from utils.permissions import IsAdmin, IsParent, IsOwnerOrAdmin, IsParentOfStudent
from utils.pagination import StandardResultsSetPagination


class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing classes
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['grade_level', 'academic_year', 'is_active']
    search_fields = ['name', 'teacher_name']
    ordering_fields = ['grade_level', 'name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all students in a class"""
        class_obj = self.get_object()
        students = class_obj.students.filter(is_active=True)
        
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current_year(self, request):
        """Get classes for current academic year"""
        from utils.helpers import get_academic_year
        
        current_year = get_academic_year()
        classes = self.get_queryset().filter(
            academic_year=current_year,
            is_active=True
        )
        
        serializer = self.get_serializer(classes, many=True)
        return Response(serializer.data)


class AreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing areas/zones
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all students in an area"""
        area = self.get_object()
        students = area.students.filter(is_active=True)
        
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def check_point(self, request):
        """Check if a point is within any area"""
        from django.contrib.gis.geos import Point
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            return Response({
                'error': 'Latitude and longitude are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        point = Point(float(lng), float(lat))
        
        areas = []
        for area in Area.objects.all():
            if area.is_point_in_area(point):
                areas.append({
                    'id': area.id,
                    'name': area.name,
                    'description': area.description
                })
        
        return Response({
            'point': {'lat': lat, 'lng': lng},
            'areas': areas
        })


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students
    """
    queryset = Student.objects.select_related(
        'class_obj', 'area', 'parent', 'parent__user'
    ).all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_obj', 'area', 'parent', 'gender', 'is_active']
    search_fields = ['student_code', 'full_name', 'parent__user__full_name']
    ordering_fields = ['full_name', 'student_code', 'date_of_birth', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        elif self.action == 'retrieve':
            return [IsAuthenticated(), IsParentOfStudent()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see their own children
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            queryset = queryset.filter(parent=user.parent_profile)
        
        # Filter by query parameters
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        
        area_id = self.request.query_params.get('area_id')
        if area_id:
            queryset = queryset.filter(area_id=area_id)
        
        has_route = self.request.query_params.get('has_route')
        if has_route == 'true':
            queryset = queryset.filter(route_assignments__is_active=True).distinct()
        elif has_route == 'false':
            queryset = queryset.exclude(route_assignments__is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        # Generate student code if not provided
        if not serializer.validated_data.get('student_code'):
            class_obj = serializer.validated_data.get('class_obj')
            if class_obj:
                from utils.helpers import generate_student_code
                last_student = Student.objects.filter(
                    class_obj=class_obj
                ).order_by('-id').first()
                
                sequence = 1
                if last_student:
                    # Extract sequence from last code
                    try:
                        sequence = int(last_student.student_code[-4:]) + 1
                    except:
                        sequence = Student.objects.count() + 1
                
                student_code = generate_student_code(
                    class_obj.grade_level,
                    sequence
                )
                serializer.save(student_code=student_code)
                return
        
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def route_info(self, request, pk=None):
        """Get student's current route assignment"""
        student = self.get_object()
        assignment = student.route_assignments.filter(
            is_active=True
        ).select_related('route', 'stop').first()
        
        if not assignment:
            return Response({
                'message': 'Student is not assigned to any route'
            })
        
        from apps.routes.serializers import StudentRouteSerializer
        serializer = StudentRouteSerializer(assignment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attendance_history(self, request, pk=None):
        """Get student's attendance history"""
        student = self.get_object()
        
        # Date range filter
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        attendances = student.attendances.select_related('trip', 'stop', 'checked_by')
        
        if from_date:
            attendances = attendances.filter(check_time__date__gte=from_date)
        if to_date:
            attendances = attendances.filter(check_time__date__lte=to_date)
        
        attendances = attendances.order_by('-check_time')[:50]
        
        from apps.attendance.serializers import AttendanceSerializer
        serializer = AttendanceSerializer(attendances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_route(self, request, pk=None):
        """Assign student to a route"""
        student = self.get_object()
        
        from apps.routes.models import StudentRoute
        from apps.routes.serializers import StudentRouteSerializer
        
        serializer = StudentRouteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=student)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def upload_photo(self, request, pk=None):
        """Upload student photo"""
        student = self.get_object()
        
        photo = request.FILES.get('photo')
        if not photo:
            return Response({
                'error': 'No photo provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student.photo = photo
        student.save()
        
        return Response({
            'message': 'Photo uploaded successfully',
            'photo_url': student.photo.url if student.photo else None
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_students': queryset.filter(is_active=True).count(),
            'by_gender': {
                'male': queryset.filter(gender='male', is_active=True).count(),
                'female': queryset.filter(gender='female', is_active=True).count(),
            },
            'by_class': list(queryset.filter(is_active=True).values(
                'class_obj__name', 'class_obj__grade_level'
            ).annotate(count=Count('id')).order_by('class_obj__grade_level')),
            'by_area': list(queryset.filter(is_active=True).values(
                'area__name'
            ).annotate(count=Count('id'))),
            'with_route': queryset.filter(
                route_assignments__is_active=True
            ).distinct().count(),
            'without_route': queryset.exclude(
                route_assignments__is_active=True
            ).count(),
        }
        
        return Response(stats)


class StudentNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student notes
    """
    queryset = StudentNote.objects.select_related('student', 'created_by').all()
    serializer_class = StudentNoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'note_type', 'is_important']
    ordering_fields = ['created_at', 'is_important']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see notes for their children
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class StudentDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student documents
    """
    queryset = StudentDocument.objects.select_related('student', 'uploaded_by').all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'document_type']
    ordering_fields = ['uploaded_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see documents for their children
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing emergency contacts
    """
    queryset = EmergencyContact.objects.select_related('student').all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'is_primary']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only manage contacts for their children
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            student_ids = user.parent_profile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset