# HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY HỆ THỐNG

## YÊU CẦU HỆ THỐNG

### Phần mềm cần cài đặt:
1. **Python 3.10+**
2. **PostgreSQL 14+ với PostGIS extension**
3. **Redis Server**
4. **OSGeo4W** (cho Windows - để có GDAL/GEOS)

## BƯỚC 1: CÀI ĐẶT POSTGRESQL VÀ POSTGIS

### Windows:
```bash
# Download và cài đặt PostgreSQL từ:
# https://www.postgresql.org/download/windows/

# Sau khi cài đặt, mở SQL Shell (psql) và chạy:
CREATE DATABASE school_bus_db;
\c school_bus_db
CREATE EXTENSION postgis;
```

### Kiểm tra PostGIS:
```sql
SELECT PostGIS_Version();
```

## BƯỚC 2: CÀI ĐẶT OSGEO4W (CHO WINDOWS)

```bash
# Download OSGeo4W từ:
# https://trac.osgeo.org/osgeo4w/

# Trong quá trình cài đặt, chọn:
# - GDAL
# - GEOS
# - PROJ

# Sau khi cài đặt, thêm vào biến môi trường PATH:
C:\OSGeo4W\bin
```

## BƯỚC 3: CÀI ĐẶT REDIS

### Windows:
```bash
# Download Redis từ:
# https://github.com/microsoftarchive/redis/releases

# Hoặc dùng Windows Subsystem for Linux (WSL)
# Hoặc dùng Docker:
docker run -d -p 6379:6379 redis
```

## BƯỚC 4: SETUP PROJECT

### 1. Clone hoặc tải project về

### 2. Tạo virtual environment:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

### 4. Tạo file .env từ .env.example:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 5. Chỉnh sửa file .env:
```env
# Cập nhật thông tin database
DB_NAME=school_bus_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Đặt SECRET_KEY mới (generate online hoặc dùng Django)
SECRET_KEY='your-secret-key-here'

# Nếu dùng Windows, thêm đường dẫn GDAL:
GDAL_LIBRARY_PATH=C:/OSGeo4W/bin/gdal306.dll
GEOS_LIBRARY_PATH=C:/OSGeo4W/bin/geos_c.dll
```

### 6. Tạo thư mục cần thiết:
```bash
mkdir -p logs media/avatars media/students media/attendance staticfiles
```

## BƯỚC 5: CHẠY MIGRATIONS

```bash
# Tạo migrations
python manage.py makemigrations

# Chạy migrations
python manage.py migrate

# Tạo superuser (nếu chưa có)
python manage.py createsuperuser
```

## BƯỚC 6: KHỞI TẠO DỮ LIỆU MẪU

```bash
python manage.py shell < scripts/init_db.py
```

## BƯỚC 7: COLLECT STATIC FILES

```bash
python manage.py collectstatic --noinput
```

## BƯỚC 8: CHẠY SERVER

### Terminal 1 - Django Server:
```bash
python manage.py runserver
```

### Terminal 2 - Celery Worker (optional):
```bash
celery -A config worker -l info
```

### Terminal 3 - Celery Beat (optional):
```bash
celery -A config beat -l info
```

### Terminal 4 - Channels (WebSocket) (optional):
```bash
daphne -b 0.0.0.0 -p 8001 config.asgi:application
```

## TRUY CẬP HỆ THỐNG

### API Documentation:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

### Admin Panel:
- URL: http://localhost:8000/admin/
- Username: admin
- Password: admin123

### API Endpoints:
- Base URL: http://localhost:8000/api/
- Auth: http://localhost:8000/api/auth/
- Students: http://localhost:8000/api/students/
- Routes: http://localhost:8000/api/routes/
- Tracking: http://localhost:8000/api/tracking/
- Attendance: http://localhost:8000/api/attendance/

## TEST API BẰNG POSTMAN

### 1. Login để lấy token:
```
POST http://localhost:8000/api/auth/login/
Body (JSON):
{
    "username": "admin",
    "password": "admin123"
}
```

### 2. Copy access token từ response

### 3. Thêm token vào Headers cho các request khác:
```
Authorization: Bearer <your_access_token>
```

## XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi: Could not find GDAL library
**Giải pháp:**
1. Cài đặt OSGeo4W
2. Thêm vào .env:
```env
GDAL_LIBRARY_PATH=C:/OSGeo4W/bin/gdal306.dll
GEOS_LIBRARY_PATH=C:/OSGeo4W/bin/geos_c.dll
```

### Lỗi: Connection refused (PostgreSQL)
**Giải pháp:**
1. Kiểm tra PostgreSQL đang chạy
2. Kiểm tra thông tin trong .env
3. Thử connect bằng psql để test

### Lỗi: Connection refused (Redis)
**Giải pháp:**
1. Khởi động Redis server
2. Windows: `redis-server.exe`
3. Linux: `sudo service redis-server start`

### Lỗi: PostGIS extension not found
**Giải pháp:**
```sql
-- Connect to database
\c school_bus_db

-- Create extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify
SELECT PostGIS_Version();
```

## KIỂM TRA HỆ THỐNG

### 1. Kiểm tra Database:
```bash
python manage.py dbshell
\dt  # List all tables
```

### 2. Kiểm tra API:
```bash
# Health check
curl http://localhost:8000/api/auth/users/
```

### 3. Kiểm tra Celery:
```bash
celery -A config inspect active
```

### 4. Kiểm tra Redis:
```bash
redis-cli ping
# Kết quả: PONG
```

## CHẠY TESTS

```bash
# Chạy tất cả tests
python manage.py test

# Chạy test cho một app cụ thể
python manage.py test apps.authentication

# Chạy với coverage
coverage run --source='.' manage.py test
coverage report
```

## NOTES

- Luôn activate virtual environment trước khi làm việc
- Backup database thường xuyên
- Kiểm tra logs trong thư mục `logs/` khi có lỗi
- Đọc API documentation tại /swagger/ để biết cách sử dụng endpoints

## HỖ TRỢ

Nếu gặp vấn đề, kiểm tra:
1. File logs/django.log
2. Console output khi chạy server
3. PostgreSQL logs
4. Redis logs