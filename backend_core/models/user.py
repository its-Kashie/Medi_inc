"""
User and Authentication Models
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Integer, JSON
from sqlalchemy.sql import func
from datetime import datetime
import enum

from backend_core.models.database import Base


class UserRole(str, enum.Enum):
    """User roles in the system"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PHARMACIST = "pharmacist"
    HOSPITAL_ADMIN = "hospital_admin"
    NIH_OFFICIAL = "nih_official"
    RESEARCHER = "researcher"
    UNIVERSITY_FOCAL = "university_focal"
    SYSTEM_ADMIN = "system_admin"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    
    # Contact information
    phone = Column(String)
    cnic = Column(String, unique=True, index=True)  # Encrypted
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Hospital/Department affiliation
    hospital_id = Column(String, index=True)
    department = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Session(Base):
    """User session model"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, nullable=False)
    refresh_token = Column(String, unique=True)
    
    # Session metadata
    ip_address = Column(String)
    user_agent = Column(String)
    device_info = Column(String)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Session {self.id} for user {self.user_id}>"


class AuditLog(Base):
    """Audit log for tracking all user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    
    # Action details
    action = Column(String, nullable=False)  # CREATE, READ, UPDATE, DELETE
    resource = Column(String, nullable=False)  # patient, prescription, etc.
    resource_id = Column(String, index=True)
    
    # Request details
    ip_address = Column(String)
    user_agent = Column(String)
    request_method = Column(String)
    request_path = Column(String)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(String)
    
    # Additional context
    details = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource} by {self.user_id}>"
