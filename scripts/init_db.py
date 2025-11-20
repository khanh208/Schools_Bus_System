# Script to initialize database with sample data
# Run: python manage.py shell --interface=python < scripts/init_db.py

from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point

from apps.authentication.models import Driver, Parent
from apps.students.models import Class, Area, Student
from apps.routes.models import Vehicle, Route, RouteStop, StudentRoute

User = get_user_model()


def create_admin():
    """Create admin user"""
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@schoolbus.com",
            password="admin123",
            full_name="System Administrator",
            role="admin",
        )
        print("Created admin user (username: admin, password: admin123)")
    else:
        print("Admin user already exists")


def create_sample_classes():
    """Create sample classes"""
    classes_data = [
        {
            "name": "1A",
            "grade_level": 1,
            "academic_year": "2024-2025",
            "teacher_name": "Nguyễn Thị A",
        },
        {
            "name": "2A",
            "grade_level": 2,
            "academic_year": "2024-2025",
            "teacher_name": "Trần Văn B",
        },
        {
            "name": "3A",
            "grade_level": 3,
            "academic_year": "2024-2025",
            "teacher_name": "Lê Thị C",
        },
    ]

    for data in classes_data:
        Class.objects.get_or_create(**data)

    print(f"Created {len(classes_data)} classes")


def create_sample_areas():
    """Create sample areas"""
    areas_data = [
        {
            "name": "Quận 1",
            "description": "Khu vực trung tâm",
        },
        {
            "name": "Quận 3",
            "description": "Khu vực quận 3",
        },
    ]

    for data in areas_data:
        Area.objects.get_or_create(name=data["name"], defaults=data)

    print(f"Created {len(areas_data)} areas")


def create_sample_parents():
    """Create sample parent users"""
    if not User.objects.filter(username="parent1").exists():
        parent1 = User.objects.create_user(
            username="parent1",
            email="parent1@example.com",
            password="parent123",
            full_name="Nguyễn Văn A",
            phone="0901234567",
            role="parent",
        )
        parent1.parent_profile.address = "123 Đường ABC, Quận 1, TP.HCM"
        parent1.parent_profile.emergency_contact = "0901234568"
        parent1.parent_profile.save()
        print("Created parent1 (username: parent1, password: parent123)")

    if not User.objects.filter(username="parent2").exists():
        parent2 = User.objects.create_user(
            username="parent2",
            email="parent2@example.com",
            password="parent123",
            full_name="Trần Thị B",
            phone="0907654321",
            role="parent",
        )
        parent2.parent_profile.address = "456 Đường XYZ, Quận 3, TP.HCM"
        parent2.parent_profile.emergency_contact = "0907654322"
        parent2.parent_profile.save()
        print("Created parent2 (username: parent2, password: parent123)")


def create_sample_drivers():
    """Create sample driver users"""
    if not User.objects.filter(username="driver1").exists():
        driver1 = User.objects.create_user(
            username="driver1",
            email="driver1@example.com",
            password="driver123",
            full_name="Phạm Văn C",
            phone="0903456789",
            role="driver",
        )
        driver1.driver_profile.license_number = "B2-12345678"
        driver1.driver_profile.license_expiry = date.today() + timedelta(days=365)
        driver1.driver_profile.experience_years = 5
        driver1.driver_profile.save()
        print("Created driver1 (username: driver1, password: driver123)")


def create_sample_vehicles():
    """Create sample vehicles"""
    vehicles_data = [
        {
            "plate_number": "51A-12345",
            "vehicle_type": "Bus",
            "capacity": 30,
            "model": "Hyundai County",
            "year": 2020,
            "insurance_expiry": date.today() + timedelta(days=180),
            "registration_expiry": date.today() + timedelta(days=365),
        },
        {
            "plate_number": "51B-67890",
            "vehicle_type": "Van",
            "capacity": 16,
            "model": "Ford Transit",
            "year": 2021,
            "insurance_expiry": date.today() + timedelta(days=180),
            "registration_expiry": date.today() + timedelta(days=365),
        },
    ]

    for data in vehicles_data:
        Vehicle.objects.get_or_create(plate_number=data["plate_number"], defaults=data)

    print(f"Created {len(vehicles_data)} vehicles")


def create_sample_students():
    """Create sample students"""
    try:
        class_1a = Class.objects.get(name="1A")
        area_q1 = Area.objects.get(name="Quận 1")
        parent1 = Parent.objects.get(user__username="parent1")

        if not Student.objects.filter(student_code="HS20240101").exists():
            Student.objects.create(
                student_code="HS20240101",
                full_name="Nguyễn Văn Anh",
                date_of_birth=date(2018, 5, 15),
                gender="male",
                class_obj=class_1a,
                area=area_q1,
                parent=parent1,
                address="123 Đường ABC, Quận 1",
                pickup_location=Point(106.6297, 10.8231),  # HCMC
                dropoff_location=Point(106.6297, 10.8231),
            )
            print("Created sample student")
    except Exception as e:
        print(f"Could not create sample student: {e}")


def create_sample_routes():
    """Create sample routes"""
    try:
        vehicle = Vehicle.objects.first()
        driver = Driver.objects.first()
        area = Area.objects.first()

        if vehicle and driver and area:
            route, created = Route.objects.get_or_create(
                route_code="R001",
                defaults={
                    "route_name": "Tuyến 1 - Quận 1",
                    "route_type": "both",
                    "vehicle": vehicle,
                    "driver": driver,
                    "area": area,
                    "estimated_duration": 45,
                },
            )

            if created:
                stops_data = [
                    {
                        "stop_order": 1,
                        "stop_name": "Điểm đón 1",
                        "location": Point(106.6297, 10.8231),
                        "estimated_arrival": time(7, 0),
                        "estimated_departure": time(7, 5),
                    },
                    {
                        "stop_order": 2,
                        "stop_name": "Trường học",
                        "location": Point(106.6397, 10.8331),
                        "estimated_arrival": time(7, 30),
                        "estimated_departure": time(7, 35),
                    },
                ]

                for stop_data in stops_data:
                    RouteStop.objects.create(route=route, **stop_data)

                print(f"Created route {route.route_code} with {len(stops_data)} stops")
    except Exception as e:
        print(f"Could not create sample route: {e}")


def main():
    """Run all initialization functions"""
    print("\n=== Initializing Database ===\n")

    create_admin()
    create_sample_classes()
    create_sample_areas()
    create_sample_parents()
    create_sample_drivers()
    create_sample_vehicles()
    create_sample_students()
    create_sample_routes()

    print("\n=== Database Initialized Successfully ===\n")
    print("You can now login with:")
    print("  Admin : username=admin, password=admin123")
    print("  Parent: username=parent1, password=parent123")
    print("  Driver: username=driver1, password=driver123")


# Khi chạy qua: python manage.py shell --interface=python < scripts/init_db.py
# file này sẽ được đọc như code thường, nên cứ gọi main() trực tiếp.
main()
