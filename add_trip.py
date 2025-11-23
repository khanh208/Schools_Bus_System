import os
import django
from django.utils import timezone
from datetime import timedelta
import random

# Cấu hình môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.authentication.models import Driver, User
from apps.routes.models import Route
from apps.tracking.models import Trip
from apps.routes.models import StudentRoute

def create_multiple_trips():
    print("🔄 Đang khởi tạo dữ liệu HÀNG LOẠT chuyến đi...")
    
    # 1. Lấy tất cả tài xế đang hoạt động
    drivers = Driver.objects.filter(user__is_active=True)
    
    if not drivers.exists():
        print("❌ Không tìm thấy tài xế nào. Hãy chạy 'python manage.py create_sample_data --clear' trước.")
        return

    print(f"found {drivers.count()} tài xế.")
    trip_count = 0
    
    print("\n" + "="*60)
    print(f"{'TRIP ID':<8} | {'LOẠI':<10} | {'TRẠNG THÁI':<12} | {'TÀI XẾ (User/Pass)':<25} | {'PHỤ HUYNH (User/Pass)'}")
    print("-" * 60)

    for driver in drivers:
        # Lấy các tuyến đường của tài xế này
        routes = Route.objects.filter(driver=driver, is_active=True)
        
        # Nếu tài xế chưa có tuyến, gán tạm 1 tuyến bất kỳ chưa có chủ hoặc dùng chung
        if not routes.exists():
            random_route = Route.objects.filter(is_active=True).first()
            if random_route:
                random_route.driver = driver
                random_route.save()
                routes = [random_route]
            else:
                continue

        for route in routes:
            today = timezone.now().date()
            
            # --- CHUYẾN 1: SÁNG (Đón) - Đang chạy ---
            # Để test tính năng Tracking ngay lập tức
            trip_morning, _ = Trip.objects.update_or_create(
                route=route,
                trip_date=today,
                trip_type='morning_pickup',
                defaults={
                    'driver': driver,
                    'vehicle': route.vehicle,
                    'scheduled_start_time': timezone.now() - timedelta(minutes=15), # Đã bắt đầu 15p trước
                    'scheduled_end_time': timezone.now() + timedelta(minutes=45),
                    'status': 'in_progress', # ĐANG CHẠY
                    'total_students': route.student_count
                }
            )
            print_trip_info(trip_morning, driver)
            trip_count += 1

            # --- CHUYẾN 2: CHIỀU (Trả) - Sắp chạy ---
            # Để test danh sách lịch trình
            trip_afternoon, _ = Trip.objects.update_or_create(
                route=route,
                trip_date=today,
                trip_type='afternoon_dropoff',
                defaults={
                    'driver': driver,
                    'vehicle': route.vehicle,
                    'scheduled_start_time': timezone.now() + timedelta(hours=4), # 4 tiếng nữa chạy
                    'scheduled_end_time': timezone.now() + timedelta(hours=5),
                    'status': 'scheduled', # SẮP CHẠY
                    'total_students': route.student_count
                }
            )
            print_trip_info(trip_afternoon, driver)
            trip_count += 1

    print("="*60)
    print(f"✅ Đã tạo/cập nhật tổng cộng {trip_count} chuyến đi.")
    print("👉 Mẹo: Dùng tài khoản Tài xế để vào chuyến 'in_progress' và gửi GPS.")
    print("👉 Mẹo: Dùng tài khoản Phụ huynh tương ứng để xem Tracking.")

def print_trip_info(trip, driver):
    # Tìm phụ huynh demo
    parent_info = "Không có HS"
    student_route = StudentRoute.objects.filter(route=trip.route, is_active=True).first()
    
    if student_route:
        parent_user = student_route.student.parent.user.username
        parent_info = f"{parent_user} / parent123"
    
    status_icon = "🟢" if trip.status == 'in_progress' else "🟡"
    
    print(f"{trip.id:<8} | {trip.trip_type.split('_')[1]:<10} | {status_icon} {trip.status:<10} | {driver.user.username:<10} / driver123   | {parent_info}")

if __name__ == "__main__":
    create_multiple_trips()