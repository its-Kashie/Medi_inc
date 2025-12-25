"""
Shared utilities for HealthLink360
"""

from shared.config import settings
from shared.logger import app_logger
from shared.pii_redaction import pii_redactor
from shared.utils import (
    generate_id,
    generate_patient_id,
    generate_prescription_id,
    generate_appointment_id,
    generate_report_id,
    format_cnic,
    format_phone,
    validate_email,
    calculate_age,
    hash_password,
    generate_secure_token,
    parse_date,
    format_date,
    get_quarter,
    get_quarter_dates,
    sanitize_filename,
    paginate,
    calculate_bmi,
    get_bmi_category,
    mask_sensitive_data
)

__all__ = [
    "settings",
    "app_logger",
    "pii_redactor",
    "generate_id",
    "generate_patient_id",
    "generate_prescription_id",
    "generate_appointment_id",
    "generate_report_id",
    "format_cnic",
    "format_phone",
    "validate_email",
    "calculate_age",
    "hash_password",
    "generate_secure_token",
    "parse_date",
    "format_date",
    "get_quarter",
    "get_quarter_dates",
    "sanitize_filename",
    "paginate",
    "calculate_bmi",
    "get_bmi_category",
    "mask_sensitive_data"
]
