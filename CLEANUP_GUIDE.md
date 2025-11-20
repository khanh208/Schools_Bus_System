
# 🚀 HƯỚNG DẪN SAU KHI CLEANUP

## 1. Xóa migrations cũ và tạo mới

```bash
# Xóa tất cả migrations
del /s /q apps\authentication\migrations\*.py
del /s /q apps\students\migrations\*.py
del /s /q apps\routes\migrations\*.py
del /s /q apps\attendance\migrations\*.py
del /s /q apps\tracking\migrations\*.py
del /s /q apps\notifications\migrations\*.py
del /s /q apps\reports\migrations\*.py

# Giữ lại __init__.py
type nul > apps\authentication\migrations\__init__.py
type nul > apps\students\migrations\__init__.py
type nul > apps\routes\migrations\__init__.py
type nul > apps\attendance\migrations\__init__.py
type nul > apps\tracking\migrations\__init__.py
type nul > apps\notifications\migrations\__init__.py
type nul > apps\reports\migrations\__init__.py

# Tạo migrations mới
python manage.py makemigrations
python manage.py migrate
```

## 2. Cập nhật requirements.txt (GIỮ LẠI CÁC PACKAGE CỐT LÕI)

```txt
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.0
django-filter==23.3
djangorestframework-simplejwt==5.3.0
psycopg2-binary==2.9.9
django-environ==0.11.2
geos==0.2.3
channels==4.0.0
channels-redis==4.1.0
uvicorn[standard]==0.24.0
websockets==12.0
redis==5.0.1
Pillow==10.1.0
drf-yasg==1.21.7
python-dateutil==2.8.2
```

## 3. Tạo lại database

```bash
# Drop và tạo lại database
psql -U postgres
DROP DATABASE school_bus_db;
CREATE DATABASE school_bus_db;
\c school_bus_db
CREATE EXTENSION postgis;
\q

# Run migrations
python manage.py migrate

# Tạo dữ liệu mẫu
python manage.py shell < scripts/init_db.py
```

## 4. Các chức năng còn lại

### ✅ AUTHENTICATION
- Login/Logout
- Change Password
- User Management (Admin/Driver/Parent)
- Profile Management

### ✅ STUDENTS
- Quản lý học sinh theo lớp
- Quản lý học sinh theo khu vực
- Gán học sinh vào tuyến đường

### ✅ ROUTES
- Quản lý tuyến đường
- Quản lý điểm dừng
- Phụ huynh tìm tuyến phù hợp theo vị trí

### ✅ ATTENDANCE
- Tài xế điểm danh lên/xuống xe
- Điểm danh vắng
- Thống kê điểm danh cơ bản

### ✅ TRACKING
- Tài xế xem lộ trình
- Phụ huynh theo dõi xe real-time
- Dự báo thời gian đến (ETA)
- Thống kê đúng giờ/trễ

### ✅ REPORTS (Simplified)
- Báo cáo điểm danh
- Báo cáo chuyến đi
- Thống kê cơ bản

### ✅ NOTIFICATIONS (Simplified)
- Thông báo điểm danh cho phụ huynh
- Thông báo xe sắp đến
- Thông báo real-time qua WebSocket

## 5. Các features ĐÃ XÓA

❌ Email notifications
❌ SMS notifications  
❌ Push notifications (Firebase)
❌ Celery background tasks
❌ Advanced reports
❌ Vehicle maintenance tracking
❌ Driver performance reports
❌ Attendance exceptions
❌ Attendance alerts
❌ Trip issues
❌ Backup/Restore (complex)
❌ Audit logs
❌ System settings
❌ Multiple notification templates
❌ Bulk notifications

## 6. Test sau khi cleanup

```bash
# Start server
python manage.py runserver

# Test endpoints
- Login: POST /api/auth/login/
- Get students: GET /api/students/students/
- Get routes: GET /api/routes/routes/
- Start trip: POST /api/tracking/trips/{id}/start/
- Check attendance: POST /api/attendance/records/check_in/
```

## 7. Cấu trúc thư mục sau cleanup

```
project/
├── apps/
│   ├── authentication/     # ✅ Core
│   ├── students/          # ✅ Core
│   ├── routes/            # ✅ Core
│   ├── attendance/        # ✅ Simplified
│   ├── tracking/          # ✅ Core
│   ├── notifications/     # ✅ Simplified (WebSocket only)
│   └── reports/           # ✅ Simplified (basic only)
├── config/
├── utils/
├── static/
├── media/
└── manage.py
```
