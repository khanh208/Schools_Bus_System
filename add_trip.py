import os
import django
from django.utils import timezone
from datetime import timedelta
import random

# Cấu hình môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.authentication.models import Driver
from apps.routes.models import Route, StudentRoute, RouteStop, Vehicle
from apps.tracking.models import Trip
from apps.students.models import Student

def create_multiple_trips():
    print("🔄 Đang khởi tạo/cập nhật dữ liệu chuyến đi...")
    
    drivers = Driver.objects.filter(user__is_active=True)
    if not drivers.exists():
        print("❌ Không tìm thấy tài xế nào.")
        return

    print(f"Tìm thấy {drivers.count()} tài xế.")
    today = timezone.now().date()
    
    print("\n" + "="*95)
    print(f"{'ID':<5} | {'LOẠI':<10} | {'TRẠNG THÁI':<12} | {'XE':<12} | {'TÀI XẾ':<15} | {'PHỤ HUYNH'}")
    print("-" * 95)

    for driver in drivers:
        # 1. Lấy tuyến đường của tài xế
        route = Route.objects.filter(driver=driver, is_active=True).first()
        
        if not route:
            # Nếu chưa có tuyến, tìm tuyến chưa có tài xế hoặc tạo đại
            route = Route.objects.filter(is_active=True).first()
            if route:
                # Update tài xế cho tuyến này để đảm bảo dữ liệu khớp
                route.driver = driver
                route.save()
            else:
                continue

        # 2. Đảm bảo tuyến có xe
        if not route.vehicle:
            # Tìm xe chưa dùng hoặc tạo mới
            vehicle = Vehicle.objects.filter(is_active=True).first()
            if not vehicle:
                vehicle = Vehicle.objects.create(
                    plate_number=f"59Z-{random.randint(10000,99999)}",
                    vehicle_type="Bus", capacity=29,
                    insurance_expiry=today + timedelta(days=365),
                    registration_expiry=today + timedelta(days=365)
                )
            route.vehicle = vehicle
            route.save()

        # 3. Đảm bảo có học sinh
        student_count = StudentRoute.objects.filter(route=route, is_active=True).count()
        if student_count == 0:
            students = Student.objects.filter(is_active=True)[:2]
            stop = RouteStop.objects.filter(route=route).first()
            if students.exists() and stop:
                for s in students:
                    StudentRoute.objects.filter(student=s, is_active=True).update(is_active=False)
                    StudentRoute.objects.create(
                        student=s, route=route, stop=stop, 
                        assignment_type='both', start_date=today
                    )
                student_count = StudentRoute.objects.filter(route=route, is_active=True).count()

        # --- TẠO/CẬP NHẬT CHUYẾN SÁNG ---
        # QUAN TRỌNG: lookup bằng (vehicle, trip_date, trip_type) để tránh lỗi Unique Vehicle
        trip_morning, created = Trip.objects.update_or_create(
            vehicle=route.vehicle,
            trip_date=today,
            trip_type='morning_pickup',
            defaults={
                'route': route,
                'driver': driver,
                'scheduled_start_time': timezone.now() - timedelta(minutes=15),
                'scheduled_end_time': timezone.now() + timedelta(minutes=45),
                'status': 'in_progress',
                'total_students': student_count
            }
        )
        print_trip_info(trip_morning, driver)

        # --- TẠO/CẬP NHẬT CHUYẾN CHIỀU ---
        trip_afternoon, created = Trip.objects.update_or_create(
            vehicle=route.vehicle,
            trip_date=today,
            trip_type='afternoon_dropoff',
            defaults={
                'route': route,
                'driver': driver,
                'scheduled_start_time': timezone.now() + timedelta(hours=4),
                'scheduled_end_time': timezone.now() + timedelta(hours=5),
                'status': 'scheduled',
                'total_students': student_count
            }
        )
        print_trip_info(trip_afternoon, driver)

    print("="*95)
    print("✅ Dữ liệu đã sẵn sàng!")

def print_trip_info(trip, driver):
    parent_info = "Không có HS"
    student_route = StudentRoute.objects.filter(route=trip.route, is_active=True).first()
    if student_route:
        parent_info = f"{student_route.student.parent.user.username} / parent123"
    
    status_icon = "🟢" if trip.status == 'in_progress' else "🟡"
    t_type = "Sáng" if "morning" in trip.trip_type else "Chiều"
    
    print(f"{trip.id:<5} | {t_type:<10} | {status_icon} {trip.status:<12} | {trip.vehicle.plate_number:<12} | {driver.user.username:<15} | {parent_info}")

if __name__ == "__main__":
    create_multiple_trips()