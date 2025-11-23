import os
import django
from django.utils import timezone
from datetime import datetime, date

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tracking.models import Trip

def fix_dates():
    # Ngày đích: 24/11/2025
    # Hoặc dùng timezone.now().date() nếu muốn lấy ngày hiện tại của máy
    target_date = date(2025, 11, 24) 
    print(f"🔄 Đang cập nhật tất cả chuyến đi sang ngày: {target_date}...")

    trips = Trip.objects.all()
    count = 0
    
    for trip in trips:
        # 1. Cập nhật ngày của chuyến
        trip.trip_date = target_date
        
        # 2. Cập nhật thời gian bắt đầu (Giữ nguyên giờ, chỉ đổi ngày)
        if trip.scheduled_start_time:
            # Lấy giờ cũ (theo múi giờ VN)
            original_time = timezone.localtime(trip.scheduled_start_time).time()
            # Ghép ngày mới + giờ cũ
            new_start = timezone.make_aware(datetime.combine(target_date, original_time))
            trip.scheduled_start_time = new_start

        # 3. Cập nhật thời gian kết thúc
        if trip.scheduled_end_time:
            original_end = timezone.localtime(trip.scheduled_end_time).time()
            new_end = timezone.make_aware(datetime.combine(target_date, original_end))
            trip.scheduled_end_time = new_end
            
        trip.save()
        count += 1

    print(f"✅ Đã cập nhật thành công {count} chuyến đi sang ngày 24/11.")

if __name__ == "__main__":
    fix_dates()