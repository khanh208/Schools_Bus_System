from datetime import datetime, timedelta
from django.utils import timezone
import random
import string


def generate_student_code(grade_level, sequence):
    """Generate unique student code"""
    year = datetime.now().year
    return f"HS{year}{grade_level:02d}{sequence:04d}"


def get_academic_year():
    """Get current academic year"""
    now = datetime.now()
    if now.month >= 9:  # September onwards is new academic year
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"


def generate_random_code(length=6):
    """Generate random alphanumeric code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def calculate_distance(point1, point2):
    """
    Calculate distance between two geographic points in kilometers
    point1, point2: tuple of (lat, lng)
    """
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r


def format_duration(minutes):
    """Format duration in minutes to human readable format"""
    if minutes < 60:
        return f"{int(minutes)} phút"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{int(hours)} giờ"
    return f"{int(hours)} giờ {int(mins)} phút"


def get_vietnamese_day_name(day_number):
    """Get Vietnamese day name from day number (0=Monday, 6=Sunday)"""
    days = {
        0: 'Thứ Hai',
        1: 'Thứ Ba',
        2: 'Thứ Tư',
        3: 'Thứ Năm',
        4: 'Thứ Sáu',
        5: 'Thứ Bảy',
        6: 'Chủ Nhật'
    }
    return days.get(day_number, '')


def is_school_day(date=None):
    """Check if given date is a school day (weekday)"""
    if date is None:
        date = timezone.now().date()
    return date.weekday() < 5  # Monday to Friday


def get_next_school_day(date=None):
    """Get next school day from given date"""
    if date is None:
        date = timezone.now().date()
    
    next_day = date + timedelta(days=1)
    while next_day.weekday() >= 5:  # Skip weekends
        next_day += timedelta(days=1)
    
    return next_day


def calculate_age(birth_date):
    """Calculate age from birth date"""
    today = timezone.now().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def format_phone_number(phone):
    """Format phone number to standard format"""
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format as Vietnamese phone number
    if len(digits) == 10 and digits.startswith('0'):
        return f"+84{digits[1:]}"
    elif len(digits) == 9:
        return f"+84{digits}"
    
    return phone


def get_time_of_day_greeting():
    """Get appropriate greeting based on time of day"""
    hour = timezone.now().hour
    
    if 5 <= hour < 12:
        return "Chào buổi sáng"
    elif 12 <= hour < 18:
        return "Chào buổi chiều"
    else:
        return "Chào buổi tối"


def parse_time_range(time_str):
    """Parse time range string like '07:00-08:00' to tuple of times"""
    try:
        start_str, end_str = time_str.split('-')
        start_time = datetime.strptime(start_str.strip(), '%H:%M').time()
        end_time = datetime.strptime(end_str.strip(), '%H:%M').time()
        return start_time, end_time
    except:
        return None, None


def is_point_near(point1, point2, threshold_meters=50):
    """
    Check if two points are near each other
    point1, point2: tuple of (lat, lng)
    threshold_meters: distance threshold in meters
    """
    distance_km = calculate_distance(point1, point2)
    distance_meters = distance_km * 1000
    return distance_meters <= threshold_meters


def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    # Remove special characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename


def generate_backup_filename():
    """Generate backup filename with timestamp"""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f"school_bus_backup_{timestamp}.sql"


def chunk_list(lst, chunk_size):
    """Split list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def get_week_date_range(date=None):
    """Get start and end date of week for given date"""
    if date is None:
        date = timezone.now().date()
    
    # Get Monday of the week
    start = date - timedelta(days=date.weekday())
    # Get Sunday of the week
    end = start + timedelta(days=6)
    
    return start, end


def get_month_date_range(date=None):
    """Get start and end date of month for given date"""
    if date is None:
        date = timezone.now().date()
    
    # First day of month
    start = date.replace(day=1)
    
    # Last day of month
    if date.month == 12:
        end = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
    
    return start, end


def validate_vietnamese_phone(phone):
    """Validate Vietnamese phone number format"""
    import re
    # Vietnamese phone patterns
    patterns = [
        r'^0[0-9]{9}$',  # 10 digits starting with 0
        r'^\+84[0-9]{9}$',  # International format
        r'^84[0-9]{9}$',  # International without +
    ]
    
    phone = phone.strip()
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    return False


def format_currency(amount):
    """Format amount as Vietnamese currency"""
    return f"{amount:,.0f} VNĐ"