"""
Common Utility Functions for HealthLink360
"""

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import secrets


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix
    
    Args:
        prefix: Prefix for the ID (e.g., "PAT", "DOC", "PRES")
    
    Returns:
        Unique ID string
    """
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{prefix}{unique_id}" if prefix else unique_id


def generate_patient_id() -> str:
    """Generate unique patient ID"""
    return generate_id("PAT-")


def generate_prescription_id() -> str:
    """Generate unique prescription ID"""
    return generate_id("PRES-")


def generate_appointment_id() -> str:
    """Generate unique appointment ID"""
    return generate_id("APT-")


def generate_report_id() -> str:
    """Generate unique report ID"""
    return generate_id("RPT-")


def format_cnic(cnic: str) -> str:
    """
    Format CNIC to standard format: 12345-1234567-1
    
    Args:
        cnic: CNIC string (with or without dashes)
    
    Returns:
        Formatted CNIC string
    """
    # Remove all non-numeric characters
    clean = re.sub(r'\D', '', cnic)
    
    if len(clean) != 13:
        raise ValueError("CNIC must be 13 digits")
    
    return f"{clean[:5]}-{clean[5:12]}-{clean[12]}"


def format_phone(phone: str, country_code: str = "+92") -> str:
    """
    Format phone number to standard format
    
    Args:
        phone: Phone number
        country_code: Country code (default: Pakistan +92)
    
    Returns:
        Formatted phone number
    """
    # Remove all non-numeric characters
    clean = re.sub(r'\D', '', phone)
    
    # Remove leading zero if present
    if clean.startswith('0'):
        clean = clean[1:]
    
    return f"{country_code}{clean}"


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address
    
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def calculate_age(date_of_birth: datetime) -> int:
    """
    Calculate age from date of birth
    
    Args:
        date_of_birth: Date of birth
    
    Returns:
        Age in years
    """
    today = datetime.now()
    age = today.year - date_of_birth.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    
    return age


def hash_password(password: str) -> str:
    """
    Hash password using SHA-256
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    
    Args:
        length: Length of the token
    
    Returns:
        Secure random token
    """
    return secrets.token_urlsafe(length)


def parse_date(date_str: str, format: str = "%Y-%m-%d") -> Optional[datetime]:
    """
    Parse date string to datetime object
    
    Args:
        date_str: Date string
        format: Date format (default: YYYY-MM-DD)
    
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, format)
    except (ValueError, TypeError):
        return None


def format_date(date: datetime, format: str = "%Y-%m-%d") -> str:
    """
    Format datetime object to string
    
    Args:
        date: Datetime object
        format: Date format (default: YYYY-MM-DD)
    
    Returns:
        Formatted date string
    """
    return date.strftime(format)


def get_quarter(date: datetime) -> int:
    """
    Get quarter number (1-4) for a given date
    
    Args:
        date: Datetime object
    
    Returns:
        Quarter number (1, 2, 3, or 4)
    """
    return (date.month - 1) // 3 + 1


def get_quarter_dates(year: int, quarter: int) -> tuple[datetime, datetime]:
    """
    Get start and end dates for a quarter
    
    Args:
        year: Year
        quarter: Quarter number (1-4)
    
    Returns:
        Tuple of (start_date, end_date)
    """
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("Quarter must be between 1 and 4")
    
    start_month = (quarter - 1) * 3 + 1
    start_date = datetime(year, start_month, 1)
    
    # Calculate end date (last day of the quarter)
    if quarter == 4:
        end_date = datetime(year, 12, 31)
    else:
        end_date = datetime(year, start_month + 3, 1) - timedelta(days=1)
    
    return start_date, end_date


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing unsafe characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove unsafe characters
    safe_filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    safe_filename = safe_filename.replace(' ', '_')
    return safe_filename


def paginate(items: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Dictionary with paginated data and metadata
    """
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        "items": items[start_idx:end_idx],
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """
    Calculate Body Mass Index (BMI)
    
    Args:
        weight_kg: Weight in kilograms
        height_m: Height in meters
    
    Returns:
        BMI value
    """
    if height_m <= 0:
        raise ValueError("Height must be greater than 0")
    return round(weight_kg / (height_m ** 2), 2)


def get_bmi_category(bmi: float) -> str:
    """
    Get BMI category
    
    Args:
        bmi: BMI value
    
    Returns:
        BMI category string
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data, showing only last few characters
    
    Args:
        data: Sensitive data string
        visible_chars: Number of characters to show at the end
    
    Returns:
        Masked string
    """
    if len(data) <= visible_chars:
        return "*" * len(data)
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]
