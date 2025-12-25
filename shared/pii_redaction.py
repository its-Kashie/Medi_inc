"""
PII Redaction Utilities for HealthLink360
Provides multi-level PII protection and anonymization
"""

import re
import hashlib
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from shared.config import settings


class PIIRedactor:
    """Handles PII redaction and anonymization"""
    
    def __init__(self):
        # Initialize encryption cipher
        self.cipher = Fernet(settings.pii_encryption_key.encode())
    
    def redact_cnic(self, cnic: str, level: int = 2) -> str:
        """
        Redact CNIC (National ID) based on level
        
        Args:
            cnic: CNIC number (format: 12345-1234567-1)
            level: Redaction level (1=partial, 2=full, 3=anonymized)
        
        Returns:
            Redacted CNIC string
        """
        if not cnic:
            return ""
        
        # Remove dashes for processing
        clean_cnic = cnic.replace("-", "")
        
        if level == 1:  # Partial - show last 4 digits
            return f"*****-*******-{clean_cnic[-4:]}"
        elif level == 2:  # Full redaction
            return "*****-*******-*"
        else:  # Level 3 - Anonymized hash
            return self._hash_value(clean_cnic)
    
    def redact_phone(self, phone: str, level: int = 2) -> str:
        """
        Redact phone number based on level
        
        Args:
            phone: Phone number
            level: Redaction level (1=partial, 2=full, 3=anonymized)
        
        Returns:
            Redacted phone string
        """
        if not phone:
            return ""
        
        # Remove non-numeric characters
        clean_phone = re.sub(r'\D', '', phone)
        
        if level == 1:  # Partial - show last 3 digits
            return f"***-***-{clean_phone[-3:]}"
        elif level == 2:  # Full redaction
            return "***-***-***"
        else:  # Level 3 - Anonymized hash
            return self._hash_value(clean_phone)
    
    def redact_email(self, email: str, level: int = 2) -> str:
        """
        Redact email address based on level
        
        Args:
            email: Email address
            level: Redaction level (1=partial, 2=full, 3=anonymized)
        
        Returns:
            Redacted email string
        """
        if not email or '@' not in email:
            return ""
        
        username, domain = email.split('@', 1)
        
        if level == 1:  # Partial - show first letter and domain
            return f"{username[0]}***@{domain}"
        elif level == 2:  # Full redaction
            return "***@***"
        else:  # Level 3 - Anonymized hash
            return self._hash_value(email)
    
    def redact_name(self, name: str, level: int = 2) -> str:
        """
        Redact person's name based on level
        
        Args:
            name: Full name
            level: Redaction level (1=partial, 2=full, 3=anonymized)
        
        Returns:
            Redacted name string
        """
        if not name:
            return ""
        
        parts = name.split()
        
        if level == 1:  # Partial - show first name initial
            return f"{parts[0][0]}. " + " ".join("*" * len(p) for p in parts[1:])
        elif level == 2:  # Full redaction
            return "***"
        else:  # Level 3 - Anonymized hash
            return f"Patient_{self._hash_value(name)[:8]}"
    
    def redact_address(self, address: str, level: int = 2) -> str:
        """
        Redact address based on level
        
        Args:
            address: Full address
            level: Redaction level (1=partial, 2=full, 3=anonymized)
        
        Returns:
            Redacted address string
        """
        if not address:
            return ""
        
        if level == 1:  # Partial - show city/region only
            # Extract last part (usually city)
            parts = address.split(',')
            return f"***, {parts[-1].strip()}" if len(parts) > 1 else "***"
        elif level == 2:  # Full redaction
            return "***"
        else:  # Level 3 - Anonymized hash
            return f"Location_{self._hash_value(address)[:8]}"
    
    def encrypt_pii(self, data: str) -> str:
        """
        Encrypt PII data for secure storage
        
        Args:
            data: Plain text PII data
        
        Returns:
            Encrypted data as string
        """
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_pii(self, encrypted_data: str) -> str:
        """
        Decrypt PII data
        
        Args:
            encrypted_data: Encrypted PII data
        
        Returns:
            Decrypted plain text
        """
        if not encrypted_data:
            return ""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def redact_patient_record(self, record: Dict[str, Any], level: int = 2) -> Dict[str, Any]:
        """
        Redact an entire patient record
        
        Args:
            record: Patient record dictionary
            level: Redaction level (1=partial, 2=full, 3=anonymized)
        
        Returns:
            Redacted record dictionary
        """
        redacted = record.copy()
        
        # Redact common PII fields
        if 'name' in redacted:
            redacted['name'] = self.redact_name(redacted['name'], level)
        if 'cnic' in redacted:
            redacted['cnic'] = self.redact_cnic(redacted['cnic'], level)
        if 'phone' in redacted:
            redacted['phone'] = self.redact_phone(redacted['phone'], level)
        if 'email' in redacted:
            redacted['email'] = self.redact_email(redacted['email'], level)
        if 'address' in redacted:
            redacted['address'] = self.redact_address(redacted['address'], level)
        
        # Remove biometric data for level 2+
        if level >= 2:
            redacted.pop('photo', None)
            redacted.pop('fingerprint', None)
            redacted.pop('biometric_data', None)
        
        return redacted
    
    def _hash_value(self, value: str) -> str:
        """Generate consistent hash for anonymization"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def verify_cnic_format(self, cnic: str) -> bool:
        """
        Verify CNIC format (Pakistani National ID)
        Format: 12345-1234567-1
        
        Args:
            cnic: CNIC string to verify
        
        Returns:
            True if valid format, False otherwise
        """
        pattern = r'^\d{5}-\d{7}-\d{1}$'
        return bool(re.match(pattern, cnic))
    
    def verify_cnic_checksum(self, cnic: str) -> bool:
        """
        Verify CNIC checksum using Luhn algorithm
        
        Args:
            cnic: CNIC string
        
        Returns:
            True if checksum is valid, False otherwise
        """
        if not self.verify_cnic_format(cnic):
            return False
        
        # Remove dashes and convert to digits
        digits = [int(d) for d in cnic.replace("-", "")]
        
        # Luhn algorithm
        checksum = 0
        for i, digit in enumerate(reversed(digits[:-1])):
            if i % 2 == 0:
                doubled = digit * 2
                checksum += doubled if doubled < 10 else doubled - 9
            else:
                checksum += digit
        
        return (checksum + digits[-1]) % 10 == 0


# Global PII redactor instance
pii_redactor = PIIRedactor()
