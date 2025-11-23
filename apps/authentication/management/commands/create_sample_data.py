# apps/authentication/management/commands/create_sample_data.py
"""
Management command to create sample data for testing
Usage: python manage.py create_sample_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import Driver, Parent
from apps.students.models import Class, Area, Student, EmergencyContact
from apps.routes.models import Vehicle, Route, RouteStop, StudentRoute, RouteSchedule
from apps.tracking.models import Trip
from django.contrib.gis.geos import Point
from datetime import date, time, timedelta
from django.utils import timezone
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing the system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()
        
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create users
        admin = self.create_admin()
        drivers = self.create_drivers(3)
        parents = self.create_parents(10)
        
        # Create school data
        classes = self.create_classes()
        areas = self.create_areas()
        
        # Create students
        students = self.create_students(parents, classes, areas)
        
        # Create vehicles and routes
        vehicles = self.create_vehicles()
        routes = self.create_routes(drivers, vehicles, areas)
        
        # Create route stops
        for route in routes:
            self.create_route_stops(route)
        
        # Assign students to routes
        self.assign_students_to_routes(students, routes)
        
        # Create trips for today
        self.create_today_trips(routes)
        
        self.stdout.write(self.style.SUCCESS('✓ Sample data created successfully!'))
        self.print_summary(admin, drivers, parents, students, routes)
    
    def clear_data(self):
        """Clear existing data"""
        # Xóa các dữ liệu liên quan trước
        Trip.objects.all().delete()
        StudentRoute.objects.all().delete()
        RouteStop.objects.all().delete()
        Route.objects.all().delete()
        Vehicle.objects.all().delete()
        Student.objects.all().delete()
        Class.objects.all().delete()
        Area.objects.all().delete()
        
        # Xóa Profile
        Parent.objects.all().delete()
        Driver.objects.all().delete()
        
        # --- PHẦN QUAN TRỌNG CẦN THÊM ---
        # Xóa luôn các User tương ứng để khi tạo lại sẽ trigger signal tạo profile mới
        User.objects.filter(username='admin').delete()
        User.objects.filter(username__startswith='driver').delete()
        User.objects.filter(username__startswith='parent').delete()
        User.objects.filter(username__startswith='test_').delete()
        
        self.stdout.write(self.style.SUCCESS('✓ Cleared all data and related users'))
    
    def create_admin(self):
        """Create admin user"""
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@schoolbus.com',
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('✓ Created admin user'))
        return admin
    
    def create_drivers(self, count):
        """Create driver users"""
        drivers = []
        driver_names = ['Nguyễn Văn Tài', 'Trần Minh Đức', 'Lê Quốc Hùng', 'Phạm Thanh Tùng']
        
        for i in range(count):
            username = f'driver{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@schoolbus.com',
                    'full_name': driver_names[i] if i < len(driver_names) else f'Tài xế {i+1}',
                    'phone': f'090{1234567 + i}',
                    'role': 'driver',
                    'is_verified': True
                }
            )
            if created:
                user.set_password('driver123')
                user.save()
                
                # Update driver profile
                user.driver_profile.license_number = f'B2-{12345678 + i}'
                user.driver_profile.license_expiry = date.today() + timedelta(days=365)
                user.driver_profile.experience_years = random.randint(2, 10)
                user.driver_profile.save()
            
            drivers.append(user.driver_profile)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} drivers'))
        return drivers
    
    def create_parents(self, count):
        """Create parent users"""
        parents = []
        parent_names = [
            'Nguyễn Thị Lan', 'Trần Văn Hải', 'Lê Thị Mai', 'Phạm Văn Nam',
            'Hoàng Thị Thu', 'Đặng Văn Sơn', 'Vũ Thị Hoa', 'Bùi Văn Toàn',
            'Đỗ Thị Nga', 'Lý Văn Kiên'
        ]
        
        for i in range(count):
            username = f'parent{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'full_name': parent_names[i] if i < len(parent_names) else f'Phụ huynh {i+1}',
                    'phone': f'091{2345678 + i}',
                    'role': 'parent',
                    'is_verified': True
                }
            )
            if created:
                user.set_password('parent123')
                user.save()
                
                # Update parent profile
                user.parent_profile.address = f'Số {10+i}, Đường {i+1}, Quận {(i%10)+1}, TP.HCM'
                user.parent_profile.emergency_contact = f'092{3456789 + i}'
                user.parent_profile.save()
            
            parents.append(user.parent_profile)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} parents'))
        return parents
    
    def create_classes(self):
        """Create classes"""
        classes_data = [
            {'name': '1A', 'grade_level': 1, 'teacher_name': 'Cô Lan Anh'},
            {'name': '1B', 'grade_level': 1, 'teacher_name': 'Cô Thu Hà'},
            {'name': '2A', 'grade_level': 2, 'teacher_name': 'Cô Minh Ngọc'},
            {'name': '3A', 'grade_level': 3, 'teacher_name': 'Thầy Văn Hùng'},
            {'name': '4A', 'grade_level': 4, 'teacher_name': 'Cô Phương Thảo'},
        ]
        
        academic_year = '2024-2025'
        classes = []
        
        for data in classes_data:
            class_obj, _ = Class.objects.get_or_create(
                name=data['name'],
                academic_year=academic_year,
                defaults={
                    'grade_level': data['grade_level'],
                    'teacher_name': data['teacher_name'],
                    'room_number': f"P{random.randint(101, 199)}",
                    'is_active': True
                }
            )
            classes.append(class_obj)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(classes)} classes'))
        return classes
    
    def create_areas(self):
        """Create areas"""
        areas_data = [
            {'name': 'Quận 1', 'description': 'Khu vực Quận 1 - Trung tâm'},
            {'name': 'Quận 3', 'description': 'Khu vực Quận 3'},
            {'name': 'Quận 10', 'description': 'Khu vực Quận 10'},
            {'name': 'Bình Thạnh', 'description': 'Khu vực Bình Thạnh'},
        ]
        
        areas = []
        for data in areas_data:
            area, _ = Area.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            areas.append(area)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(areas)} areas'))
        return areas
    
    def create_students(self, parents, classes, areas):
        """Create students"""
        students = []
        first_names = ['An', 'Bình', 'Cường', 'Dũng', 'Hà', 'Hương', 'Linh', 'Mai', 'Nam', 'Oanh']
        last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng']
        
        # HCMC coordinates ranges
        lat_range = (10.7, 10.9)
        lng_range = (106.6, 106.8)
        
        for i, parent in enumerate(parents):
            # Each parent has 1-2 children
            num_children = random.randint(1, 2)
            
            for j in range(num_children):
                last_name = random.choice(last_names)
                first_name = random.choice(first_names)
                full_name = f'{last_name} Văn {first_name}'
                
                student_code = f'HS{2024}{random.randint(10, 99)}{i:03d}{j}'
                
                birth_year = random.randint(2016, 2020)
                birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
                
                # Random location in HCMC
                pickup_lat = random.uniform(*lat_range)
                pickup_lng = random.uniform(*lng_range)
                
                student, created = Student.objects.get_or_create(
                    student_code=student_code,
                    defaults={
                        'full_name': full_name,
                        'date_of_birth': birth_date,
                        'gender': random.choice(['male', 'female']),
                        'class_obj': random.choice(classes),
                        'area': random.choice(areas),
                        'parent': parent,
                        'address': f'{parent.address}',
                        'pickup_location': Point(pickup_lng, pickup_lat),
                        'dropoff_location': Point(pickup_lng + 0.01, pickup_lat + 0.01),
                        'blood_type': random.choice(['A', 'B', 'O', 'AB']),
                        'is_active': True
                    }
                )
                
                if created:
                    # Create emergency contact
                    EmergencyContact.objects.create(
                        student=student,
                        name=parent.user.full_name,
                        relationship='Phụ huynh',
                        phone=parent.user.phone,
                        is_primary=True
                    )
                
                students.append(student)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(students)} students'))
        return students
    
    def create_vehicles(self):
        """Create vehicles"""
        vehicles_data = [
            {'plate': '51A-123.45', 'type': 'Bus 29 chỗ', 'capacity': 29, 'model': 'Hyundai County'},
            {'plate': '51B-678.90', 'type': 'Bus 29 chỗ', 'capacity': 29, 'model': 'Hyundai County'},
            {'plate': '51C-111.22', 'type': 'Van 16 chỗ', 'capacity': 16, 'model': 'Ford Transit'},
        ]
        
        vehicles = []
        for data in vehicles_data:
            vehicle, _ = Vehicle.objects.get_or_create(
                plate_number=data['plate'],
                defaults={
                    'vehicle_type': data['type'],
                    'capacity': data['capacity'],
                    'model': data['model'],
                    'year': random.randint(2019, 2023),
                    'color': random.choice(['Trắng', 'Vàng', 'Xanh']),
                    'insurance_expiry': date.today() + timedelta(days=180),
                    'registration_expiry': date.today() + timedelta(days=365),
                    'status': 'active',
                    'is_active': True
                }
            )
            vehicles.append(vehicle)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(vehicles)} vehicles'))
        return vehicles
    
    def create_routes(self, drivers, vehicles, areas):
        """Create routes"""
        routes = []
        route_types = ['pickup', 'dropoff']
        
        for i, (driver, vehicle, area) in enumerate(zip(drivers, vehicles, areas[:len(drivers)])):
            for route_type in route_types:
                route_code = f'R{i+1:02d}-{route_type[0].upper()}'
                route_name = f'Tuyến {i+1} - {area.name} ({route_type})'
                
                route, _ = Route.objects.get_or_create(
                    route_code=route_code,
                    defaults={
                        'route_name': route_name,
                        'route_type': route_type,
                        'area': area,
                        'vehicle': vehicle,
                        'driver': driver,
                        'estimated_duration': random.randint(30, 60),
                        'is_active': True
                    }
                )
                routes.append(route)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(routes)} routes'))
        return routes
    
    def create_route_stops(self, route):
        """Create stops for a route"""
        num_stops = random.randint(3, 6)
        
        # Base coordinates
        base_lat = 10.8
        base_lng = 106.7
        
        for i in range(num_stops):
            stop_lat = base_lat + (i * 0.01)
            stop_lng = base_lng + (i * 0.01)
            
            start_hour = 7 if route.route_type == 'pickup' else 16
            arrival_time = time(start_hour, i * 10)
            departure_time = time(start_hour, i * 10 + 5)
            
            RouteStop.objects.get_or_create(
                route=route,
                stop_order=i + 1,
                defaults={
                    'stop_name': f'Điểm dừng {i+1} - {route.area.name}',
                    'location': Point(stop_lng, stop_lat),
                    'address': f'Số {100 + i*10}, Đường {i+1}, {route.area.name}',
                    'estimated_arrival': arrival_time,
                    'estimated_departure': departure_time,
                    'stop_duration': 5,
                    'is_active': True
                }
            )
    
    def assign_students_to_routes(self, students, routes):
        """Assign students to routes"""
        count = 0
        for student in students:
            # Find routes in student's area
            area_routes = [r for r in routes if r.area == student.area]
            
            if area_routes:
                # Assign to pickup route
                pickup_route = random.choice([r for r in area_routes if r.route_type == 'pickup'])
                pickup_stop = pickup_route.stops.first()
                
                if pickup_stop:
                    StudentRoute.objects.get_or_create(
                        student=student,
                        route=pickup_route,
                        stop=pickup_stop,
                        assignment_type='pickup',
                        defaults={
                            'start_date': date.today(),
                            'is_active': True
                        }
                    )
                    count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {count} students to routes'))
    
    def create_today_trips(self, routes):
        """Create trips for today"""
        today = timezone.now().date()
        morning_time = timezone.datetime.combine(today, time(7, 0))
        afternoon_time = timezone.datetime.combine(today, time(16, 0))
        
        trips = []
        for route in routes:
            trip_type = 'morning_pickup' if route.route_type == 'pickup' else 'afternoon_dropoff'
            start_time = morning_time if route.route_type == 'pickup' else afternoon_time
            
            # Count students on route
            student_count = StudentRoute.objects.filter(
                route=route,
                is_active=True
            ).count()
            
            trip, created = Trip.objects.get_or_create(
                route=route,
                trip_date=today,
                trip_type=trip_type,
                defaults={
                    'driver': route.driver,
                    'vehicle': route.vehicle,
                    'scheduled_start_time': start_time,
                    'scheduled_end_time': start_time + timedelta(hours=1),
                    'status': 'scheduled',
                    'total_students': student_count
                }
            )
            if created:
                trips.append(trip)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(trips)} trips for today'))
    
    def print_summary(self, admin, drivers, parents, students, routes):
        """Print summary of created data"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SAMPLE DATA SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Admin Users: 1')
        self.stdout.write(f'Drivers: {len(drivers)}')
        self.stdout.write(f'Parents: {len(parents)}')
        self.stdout.write(f'Students: {len(students)}')
        self.stdout.write(f'Routes: {len(routes)}')
        self.stdout.write('='*60)
        self.stdout.write('\nLogin credentials:')
        self.stdout.write(self.style.SUCCESS('  Admin: username=admin, password=admin123'))
        self.stdout.write(self.style.SUCCESS('  Driver: username=driver1, password=driver123'))
        self.stdout.write(self.style.SUCCESS('  Parent: username=parent1, password=parent123'))
        self.stdout.write('='*60 + '\n')