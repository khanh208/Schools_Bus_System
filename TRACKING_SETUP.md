# 🚀 Hướng dẫn cài đặt Real-time Tracking cho Phụ huynh

## 📋 Tổng quan thay đổi

Đã thay thế **Daphne** bằng **Uvicorn** để chạy ASGI server với WebSocket support tốt hơn.

---

## 🔧 Bước 1: Cài đặt dependencies mới

```bash
# Activate virtual environment
venv\Scripts\activate

# Cài đặt packages mới
pip install uvicorn[standard]==0.24.0
pip install websockets==12.0

# Hoặc cài tất cả từ requirements.txt
pip install -r requirements.txt
```

---

## 📁 Bước 2: Thêm file mới vào project

### 2.1. Tạo Parent Tracking View
Tạo file: `apps/tracking/parent_views.py`

```python
# Copy nội dung từ artifact "Parent Tracking API View"
```

### 2.2. Cập nhật URLs
Thêm vào `apps/tracking/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, LocationLogViewSet, StopArrivalViewSet, TripIssueViewSet
from .parent_views import ParentTrackingViewSet, parent_tracking_page, parent_tracking_demo

router = DefaultRouter()
router.register('trips', TripViewSet, basename='trip')
router.register('locations', LocationLogViewSet, basename='location-log')
router.register('stop-arrivals', StopArrivalViewSet, basename='stop-arrival')
router.register('issues', TripIssueViewSet, basename='trip-issue')

# Parent tracking
router.register('parent/tracking', ParentTrackingViewSet, basename='parent-tracking')

urlpatterns = [
    path('', include(router.urls)),
    
    # Parent tracking pages
    path('parent/map/', parent_tracking_page, name='parent-tracking-page'),
    path('parent/demo/', parent_tracking_demo, name='parent-tracking-demo'),
]
```

### 2.3. Tạo template folder
```bash
mkdir templates\tracking
```

### 2.4. Lưu Parent Tracking HTML
Lưu nội dung từ artifact "Parent Real-time Tracking Interface" vào:
- `templates/tracking/parent_tracking.html` (cần auth)
- `templates/tracking/parent_tracking_demo.html` (demo không cần auth)

---

## 🎯 Bước 3: Cấu hình Settings

Đảm bảo `config/settings.py` có:

```python
# ASGI Application
ASGI_APPLICATION = 'config.asgi.application'

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# CORS - Thêm WebSocket support
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'sec-websocket-protocol',
]
```

---

## 🚀 Bước 4: Chạy server

### Cách 1: Dùng script tự động (Windows)
```bash
run_server.bat
```

### Cách 2: Chạy thủ công

#### Terminal 1 - Main Server với Uvicorn
```bash
venv\Scripts\activate
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload --ws websockets
```

#### Terminal 2 - Celery Worker (Optional)
```bash
venv\Scripts\activate
celery -A config worker -l info
```

#### Terminal 3 - Celery Beat (Optional)
```bash
venv\Scripts\activate
celery -A config beat -l info
```

---

## 🧪 Bước 5: Test WebSocket

### Test 1: Kiểm tra WebSocket endpoint
```javascript
// Mở Console trong browser (F12)
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');

ws.onopen = () => console.log('✓ WebSocket connected');
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));
ws.onerror = (e) => console.error('WebSocket error:', e);
```

### Test 2: Truy cập trang tracking

#### Demo page (không cần login):
```
http://localhost:8000/api/tracking/parent/demo/
```

#### Authenticated page:
1. Login để lấy token:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"parent1","password":"parent123"}'
```

2. Truy cập với token:
```
http://localhost:8000/api/tracking/parent/map/?token=YOUR_ACCESS_TOKEN
```

---

## 📡 API Endpoints cho Parent

### 1. Lấy danh sách trips đang hoạt động
```http
GET /api/tracking/parent/tracking/active/
Authorization: Bearer {token}
```

### 2. Xem vị trí real-time của trip
```http
GET /api/tracking/parent/tracking/{trip_id}/live_location/
Authorization: Bearer {token}
```

### 3. Lấy trạng thái con em
```http
GET /api/tracking/parent/tracking/my_children_status/
Authorization: Bearer {token}
```

### 4. Tính ETA đến điểm đón
```http
GET /api/tracking/parent/tracking/{trip_id}/eta/?student_id={student_id}
Authorization: Bearer {token}
```

---

## 🔍 Kiểm tra hệ thống

### Checklist:
- [ ] Redis đang chạy (port 6379)
- [ ] PostgreSQL đang chạy (port 5432)
- [ ] Uvicorn server chạy thành công
- [ ] WebSocket connection thành công
- [ ] Map hiển thị đúng
- [ ] Thông báo real-time hoạt động

### Test Redis:
```bash
redis-cli ping
# Kết quả: PONG
```

### Test PostgreSQL:
```bash
psql -U postgres -c "SELECT 1"
# Kết quả: 1
```

### Xem logs:
```bash
# Logs trong terminal chạy uvicorn
# Hoặc xem file logs
type logs\django.log
```

---

## 🎨 Tính năng Parent Tracking

### ✅ Đã có:
1. **Real-time location tracking**
   - Hiển thị vị trí xe bus trên bản đồ
   - Cập nhật tự động mỗi vài giây

2. **WebSocket notifications**
   - Thông báo điểm danh
   - Cảnh báo xe sắp đến
   - Cập nhật trạng thái chuyến đi

3. **ETA calculation**
   - Tính thời gian đến điểm dừng
   - Hiển thị khoảng cách còn lại

4. **Student status**
   - Xem trạng thái tất cả con
   - Lịch sử điểm danh
   - Thông tin tuyến đường

5. **Interactive map**
   - Zoom in/out
   - Pan around
   - Click markers cho chi tiết

### 🎯 UI Features:
- Responsive design (mobile-friendly)
- Auto-reconnect WebSocket
- Real-time notifications
- Connection status indicator
- Manual refresh button

---

## 🐛 Xử lý lỗi thường gặp

### Lỗi 1: WebSocket connection failed
**Nguyên nhân:** Redis chưa chạy
**Giải pháp:**
```bash
# Windows
redis-server.exe

# hoặc dùng Docker
docker run -d -p 6379:6379 redis
```

### Lỗi 2: ASGI application not found
**Nguyên nhân:** Import sai trong asgi.py
**Giải pháp:** Kiểm tra `config/asgi.py`:
```python
from apps.tracking.consumers import TripTrackingConsumer, ParentNotificationConsumer
```

### Lỗi 3: CORS error
**Giải pháp:** Thêm vào settings.py:
```python
CORS_ALLOW_ALL_ORIGINS = True  # Chỉ cho development
CORS_ALLOW_CREDENTIALS = True
```

### Lỗi 4: 403 Forbidden
**Nguyên nhân:** Token expired hoặc không hợp lệ
**Giải pháp:** Login lại để lấy token mới

---

## 📱 Mobile Support

Interface đã responsive, có thể truy cập từ:
- Desktop browser
- Tablet
- Mobile browser

**Lưu ý:** Để test trên mobile trong cùng mạng:
1. Tìm IP máy tính: `ipconfig`
2. Truy cập: `http://192.168.x.x:8000/api/tracking/parent/demo/`

---

## 🔐 Security Notes

### Production checklist:
- [ ] Đổi SECRET_KEY
- [ ] Tắt DEBUG
- [ ] Cấu hình ALLOWED_HOSTS
- [ ] Bật HTTPS
- [ ] Cấu hình CORS đúng domain
- [ ] Rate limiting cho WebSocket
- [ ] Authentication cho tất cả endpoints

---

## 📊 Performance Tips

1. **Redis optimization:**
   - Tăng `maxmemory` nếu có nhiều connections
   - Monitor memory usage

2. **WebSocket connections:**
   - Giới hạn số connections per user
   - Implement heartbeat/ping-pong

3. **Database queries:**
   - Sử dụng select_related
   - Cache thông tin thường xuyên truy cập

4. **Location updates:**
   - Buffer updates (gửi mỗi 5-10 giây thay vì real-time)
   - Throttle GPS updates từ driver app

---

## 📚 Tài liệu thêm

- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [Leaflet.js](https://leafletjs.com/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## ✅ Hoàn thành!

Giờ đây hệ thống đã có đầy đủ:
1. ✅ Backend API với Django REST Framework
2. ✅ Real-time tracking với WebSocket (Uvicorn)
3. ✅ Interactive map với Leaflet
4. ✅ Parent notification system
5. ✅ ETA calculation
6. ✅ Attendance tracking
7. ✅ Trip management

**Next steps:**
- Tạo mobile app (React Native/Flutter)
- Thêm push notifications (Firebase)
- Implement offline mode
- Add analytics dashboard