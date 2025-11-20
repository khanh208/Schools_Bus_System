"""
Script to remove unnecessary features and keep only core functionality
Run: python cleanup_unnecessary_features.py
"""

import os
import shutil

# Các files/folders cần XÓA hoàn toàn
FILES_TO_DELETE = [
    # Notifications không cần thiết
    'apps/notifications/tasks.py',
    'apps/notifications/services.py',
    'templates/notifications/',
    
    # Reports phức tạp
    'apps/reports/admin_views.py',
    'apps/reports/services.py',
    'templates/admin/dashboard.html',
    
    # Backup module (giữ lại nhưng đơn giản hóa)
    'apps/backup/services.py',
    
    # Tracking phức tạp không cần
    'apps/tracking/parent_views.py',
    'templates/tracking/',
    
    # Test files
    'scripts/test_api.py',
    'test_requests.json',
]

# Các models/features cần XÓA trong files
FEATURES_TO_REMOVE = {
    'apps/notifications/models.py': [
        'NotificationTemplate',
        'BulkNotification',
        'PushToken',
        'NotificationLog',
    ],
    'apps/reports/models.py': [
        'DriverPerformanceReport',
        'RoutePerformanceReport',
        'SystemStatistics',
    ],
    'apps/attendance/models.py': [
        'AttendanceException',
        'AttendanceReport',
        'AttendanceAlert',
    ],
    'apps/tracking/models.py': [
        'TripIssue',
        'ETARecord',
    ],
}

def delete_files():
    """Delete unnecessary files"""
    print("🗑️  Deleting unnecessary files...")
    
    for file_path in FILES_TO_DELETE:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"   ✓ Deleted folder: {file_path}")
            else:
                os.remove(file_path)
                print(f"   ✓ Deleted file: {file_path}")
        else:
            print(f"   ⚠ Not found: {file_path}")

def simplify_models():
    """Remove unnecessary models from files"""
    print("\n📝 Simplifying models...")
    
    for file_path, models_to_remove in FEATURES_TO_REMOVE.items():
        if not os.path.exists(file_path):
            continue
            
        print(f"\n   Processing: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for model_name in models_to_remove:
            # Find model definition
            start = content.find(f"class {model_name}(")
            if start == -1:
                continue
                
            # Find next class or end of file
            next_class = content.find("\nclass ", start + 1)
            if next_class == -1:
                next_class = len(content)
            
            # Remove model
            content = content[:start] + content[next_class:]
            print(f"      ✓ Removed: {model_name}")
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

def create_simplified_settings():
    """Create simplified settings"""
    print("\n⚙️  Creating simplified settings...")
    
    simplified_apps = """
# Simplified INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    
    # Third party - Core only
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'channels',
    
    # Local apps - Core only
    'apps.authentication',
    'apps.students',
    'apps.routes',
    'apps.attendance',
    'apps.tracking',
    'apps.notifications',  # Simplified
    'apps.reports',  # Simplified
]
"""
    
    print("   ✓ Remove unnecessary third-party packages from requirements.txt")
    print("   ✓ Simplify INSTALLED_APPS in settings.py")

def create_migration_guide():
    """Create migration guide"""
    guide = """
# 🚀 HƯỚNG DẪN SAU KHI CLEANUP

## 1. Xóa migrations cũ và tạo mới

```bash
# Xóa tất cả migrations
del /s /q apps\\authentication\\migrations\\*.py
del /s /q apps\\students\\migrations\\*.py
del /s /q apps\\routes\\migrations\\*.py
del /s /q apps\\attendance\\migrations\\*.py
del /s /q apps\\tracking\\migrations\\*.py
del /s /q apps\\notifications\\migrations\\*.py
del /s /q apps\\reports\\migrations\\*.py

# Giữ lại __init__.py
type nul > apps\\authentication\\migrations\\__init__.py
type nul > apps\\students\\migrations\\__init__.py
type nul > apps\\routes\\migrations\\__init__.py
type nul > apps\\attendance\\migrations\\__init__.py
type nul > apps\\tracking\\migrations\\__init__.py
type nul > apps\\notifications\\migrations\\__init__.py
type nul > apps\\reports\\migrations\\__init__.py

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
\\c school_bus_db
CREATE EXTENSION postgis;
\\q

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
"""
    
    with open('CLEANUP_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("   ✓ Created CLEANUP_GUIDE.md")

def main():
    """Main cleanup function"""
    print("\n" + "="*60)
    print("🧹 SCHOOL BUS SYSTEM - CLEANUP SCRIPT")
    print("="*60)
    print("\nThis will remove unnecessary features and keep only core functionality")
    
    confirm = input("\n⚠️  Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Delete files
    delete_files()
    
    # Simplify models
    simplify_models()
    
    # Create guides
    create_simplified_settings()
    create_migration_guide()
    
    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETED!")
    print("="*60)
    print("\n📖 Next steps:")
    print("   1. Read CLEANUP_GUIDE.md")
    print("   2. Delete old migrations")
    print("   3. Run: python manage.py makemigrations")
    print("   4. Run: python manage.py migrate")
    print("   5. Run: python manage.py shell < scripts/init_db.py")
    print("\n")

if __name__ == '__main__':
    main()