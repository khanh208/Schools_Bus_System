# School Bus Management System - API Documentation

## 🔐 Authentication

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "role": "admin"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Get Profile
```http
GET /api/auth/profile/
Authorization: Bearer {access_token}
```

## 👥 Users Management

### List Users (Admin only)
```http
GET /api/auth/users/
Authorization: Bearer {access_token}
```

### Create User
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "driver2",
  "email": "driver2@example.com",
  "password": "driver123",
  "password_confirm": "driver123",
  "full_name": "Nguyễn Văn B",
  "phone": "0912345678",
  "role": "driver",
  "license_number": "B2-87654321",
  "license_expiry": "2025-12-31"
}
```

## 👦 Students

### List Students
```http
GET /api/students/students/
Authorization: Bearer {access_token}

Query params:
- page: số trang (default: 1)
- page_size: số record/trang (default: 20)
- class_id: lọc theo lớp
- area_id: lọc theo khu vực
- search: tìm kiếm theo tên, mã học sinh
```

### Get Student Detail
```http
GET /api/students/students/{id}/
Authorization: Bearer {access_token}
```

### Create Student
```http
POST /api/students/students/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "student_code": "HS20240002",
  "full_name": "Trần Thị Bình",
  "date_of_birth": "2018-03-20",
  "gender": "female",
  "class_obj": 1,
  "area": 1,
  "parent": 1,
  "address": "456 Đường XYZ, Quận 3",
  "pickup_lat": 10.7756,
  "pickup_lng": 106.7008,
  "dropoff_lat": 10.7756,
  "dropoff_lng": 106.7008
}
```

## 🚌 Routes

### List Routes
```http
GET /api/routes/routes/
Authorization: Bearer {access_token}
```

### Get Route Detail with Stops
```http
GET /api/routes/routes/{id}/
Authorization: Bearer {access_token}
```

### Get Route Stops
```http
GET /api/routes/routes/{id}/stops/
Authorization: Bearer {access_token}
```

## 🚗 Trips

### List Trips
```http
GET /api/tracking/trips/
Authorization: Bearer {access_token}

Query params:
- trip_date: lọc theo ngày (YYYY-MM-DD)
- status: scheduled, in_progress, completed, cancelled
- route: lọc theo tuyến
```

### Get Today's Trips
```http
GET /api/tracking/trips/today/
Authorization: Bearer {access_token}
```

### Start Trip (Driver)
```http
POST /api/tracking/trips/{id}/start/
Authorization: Bearer {driver_access_token}
```

### Complete Trip (Driver)
```http
POST /api/tracking/trips/{id}/complete/
Authorization: Bearer {driver_access_token}
```

### Get Trip Tracking (Real-time)
```http
GET /api/tracking/trips/{id}/tracking/
Authorization: Bearer {access_token}
```

## ✅ Attendance

### Check-in Student
```http
POST /api/attendance/records/check_in/
Authorization: Bearer {driver_access_token}
Content-Type: application/json

{
  "trip": 1,
  "student": 1,
  "stop": 1,
  "attendance_type": "check_in",
  "status": "present",
  "lat": 10.7756,
  "lng": 106.7008
}
```

### Bulk Check-in
```http
POST /api/attendance/records/bulk_check_in/
Authorization: Bearer {driver_access_token}
Content-Type: application/json

{
  "trip_id": 1,
  "attendance_records": [
    {"student_id": 1, "status": "present"},
    {"student_id": 2, "status": "absent"}
  ]
}
```

### Get Attendance Statistics
```http
GET /api/attendance/records/statistics/
Authorization: Bearer {access_token}

Query params:
- from_date: YYYY-MM-DD
- to_date: YYYY-MM-DD
```

## 🔔 Notifications

### Get User Notifications
```http
GET /api/notifications/notifications/
Authorization: Bearer {access_token}
```

### Get Unread Notifications
```http
GET /api/notifications/notifications/unread/
Authorization: Bearer {access_token}
```

### Mark as Read
```http
POST /api/notifications/notifications/mark_as_read/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "notification_ids": [1, 2, 3]
}
```

## 📊 Reports

### Get Daily Report
```http
GET /api/reports/daily/{date}/
Authorization: Bearer {access_token}
```

### Generate Attendance Report
```http
POST /api/reports/attendance/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "student_id": 1,
  "start_date": "2024-11-01",
  "end_date": "2024-11-30",
  "report_type": "monthly"
}
```

## 🔒 Authorization

**Roles:**
- `admin`: Full access
- `driver`: Access to trips, routes, attendance
- `parent`: Access to their children's information only

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

## ⚠️ Error Codes

- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Invalid or missing token
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `500`: Internal Server Error