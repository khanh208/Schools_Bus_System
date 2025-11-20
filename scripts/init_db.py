# scripts/init_db.py
# Safe DB init script

from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point

from apps.authentication.models import Parent, Driver
from apps.students.models import Class, Area, Student
from apps.routes.models import Vehicle, Route, RouteStop

User = get_user_model()


def main():
    print("=== Initializing Database ===")

    # 1. Admin user
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@schoolbus.com",
            password="admin123",
        )
        print("Created admin user (username=admin, password=admin123)")
    else:
        print("Admin user already exists")

    # 2. Classes
    classes_data = [
        {"name": "1A", "grade_level": 1, "academic_year": "2024-2025", "teacher_name": "Teacher A"},
        {"name": "2A", "grade_level": 2, "academic_year": "2024-2025", "teacher_name": "Teacher B"},
        {"name": "3A", "grade_level": 3, "academic_year": "2024-2025", "teacher_name": "Teacher C"},
    ]

    for data in classes_data:
        Class.objects.get_or_create(**data)
    print(f"Created {len(classes_data)} classes")

    # 3. Areas
    areas_data = [
        {"name": "Area 1", "description": "Center area"},
        {"name": "Area 3", "description": "Area 3 zone"},
    ]

    for data in areas_data:
        Area.objects.get_or_create(name=data["name"], defaults=data)
    print(f"Created {len(areas_data)} areas")

    # 4. Parents
    if not User.objects.filter(username="parent1").exists():
        parent1_user = User.objects.create_user(
            username="parent1",
            email="parent1@example.com",
            password="parent123",
            full_name="Parent One",
            phone="0901234567",
            role="parent",
        )
        parent1 = Parent.objects.get(user=parent1_user)
        parent1.address = "123 ABC Street"
        parent1.emergency_contact = "0901234568"
        parent1.save()
        print("Created parent1 (username=parent1, password=parent123)")

    if not User.objects.filter(username="parent2").exists():
        parent2_user = User.objects.create_user(
            username="parent2",
            email="parent2@example.com",
            password="parent123",
            full_name="Parent Two",
            phone="0907654321",
            role="parent",
        )
        parent2 = Parent.objects.get(user=parent2_user)
        parent2.address = "456 XYZ Street"
        parent2.emergency_contact = "0907654322"
        parent2.save()
        print("Created parent2 (username=parent2, password=parent123)")

    # 5. Driver
    if not User.objects.filter(username="driver1").exists():
        driver_user = User.objects.create_user(
            username="driver1",
            email="driver1@example.com",
            password="driver123",
            full_name="Driver One",
            phone="0903456789",
            role="driver",
        )
        driver = Driver.objects.get(user=driver_user)
        driver.license_number = "B2-12345678"
        driver.license_expiry = date.today() + timedelta(days=365)
        driver.experience_years = 5
        driver.save()
        print("Created driver1 (username=driver1, password=driver123)")

    # 6. Vehicles
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

    # 7. One sample student
    try:
        class_1a = Class.objects.get(name="1A")
        area_1 = Area.objects.get(name="Area 1")
        parent1 = Parent.objects.get(user__username="parent1")

        if not Student.objects.filter(student_code="HS20240101").exists():
            Student.objects.create(
                student_code="HS20240101",
                full_name="Student One",
                date_of_birth=date(2018, 5, 15),
                gender="male",
                class_obj=class_1a,
                area=area_1,
                parent=parent1,
                address="123 ABC Street",
                pickup_location=Point(106.6297, 10.8231),
                dropoff_location=Point(106.6297, 10.8231),
            )
            print("Created sample student")
    except Exception as e:
        print(f"Could not create sample student: {e}")

    # 8. One sample route
    try:
        vehicle = Vehicle.objects.first()
        driver = Driver.objects.first()
        area = Area.objects.first()

        if vehicle and driver and area:
            route, created = Route.objects.get_or_create(
                route_code="R001",
                defaults={
                    "route_name": "Route 1 - Area 1",
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
                        "stop_name": "Stop 1",
                        "location": Point(106.6297, 10.8231),
                        "estimated_arrival": time(7, 0),
                        "estimated_departure": time(7, 5),
                    },
                    {
                        "stop_order": 2,
                        "stop_name": "School",
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

    print("=== Database Initialized Successfully ===")
    print("Admin  : admin / admin123")
    print("Parent : parent1 / parent123")
    print("Driver : driver1 / driver123")
