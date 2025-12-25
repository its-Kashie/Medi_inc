"""
Patient and Medical Record Models
"""

from sqlalchemy import Column, String, Date, DateTime, Float, Integer, Boolean, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from backend_core.models.database import Base


class BloodGroup(str, enum.Enum):
    """Blood group types"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class Gender(str, enum.Enum):
    """Gender types"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"
    
    # Primary identifiers
    id = Column(String, primary_key=True, index=True)
    cnic = Column(String, unique=True, index=True)  # Encrypted
    medical_record_number = Column(String, unique=True, index=True)
    
    # Personal information (Encrypted)
    full_name = Column(String, nullable=False)  # Encrypted
    date_of_birth = Column(Date, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    blood_group = Column(SQLEnum(BloodGroup))
    
    # Contact information (Encrypted)
    phone = Column(String)  # Encrypted
    email = Column(String)  # Encrypted
    address = Column(Text)  # Encrypted
    city = Column(String)
    province = Column(String)
    postal_code = Column(String)
    
    # Emergency contact (Encrypted)
    emergency_contact_name = Column(String)  # Encrypted
    emergency_contact_phone = Column(String)  # Encrypted
    emergency_contact_relation = Column(String)
    
    # Medical information
    height_cm = Column(Float)
    weight_kg = Column(Float)
    bmi = Column(Float)
    
    # Allergies and conditions
    allergies = Column(JSON)  # List of allergies
    chronic_conditions = Column(JSON)  # List of chronic conditions
    current_medications = Column(JSON)  # List of current medications
    
    # Insurance information
    insurance_provider = Column(String)
    insurance_number = Column(String)  # Encrypted
    insurance_expiry = Column(Date)
    
    # Hospital affiliation
    primary_hospital_id = Column(String, index=True)
    primary_doctor_id = Column(String, index=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deceased = Column(Boolean, default=False)
    date_of_death = Column(Date)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_visit = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Patient {self.id} - {self.medical_record_number}>"


class MedicalRecord(Base):
    """Medical record/visit model"""
    __tablename__ = "medical_records"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), index=True, nullable=False)
    
    # Visit information
    visit_date = Column(DateTime(timezone=True), nullable=False, index=True)
    visit_type = Column(String)  # outpatient, emergency, inpatient, etc.
    department = Column(String, index=True)
    hospital_id = Column(String, index=True)
    
    # Medical staff
    doctor_id = Column(String, index=True)
    nurse_id = Column(String)
    
    # Chief complaint and diagnosis
    chief_complaint = Column(Text)
    diagnosis = Column(Text)
    icd_10_codes = Column(JSON)  # List of ICD-10 codes
    
    # Vitals
    temperature_c = Column(Float)
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    heart_rate = Column(Integer)
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Float)
    
    # Clinical notes
    history_of_present_illness = Column(Text)
    physical_examination = Column(Text)
    assessment = Column(Text)
    plan = Column(Text)
    
    # Prescriptions and orders
    prescriptions = Column(JSON)  # List of prescribed medications
    lab_orders = Column(JSON)  # List of lab tests ordered
    imaging_orders = Column(JSON)  # List of imaging studies ordered
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_notes = Column(Text)
    
    # Status
    status = Column(String, default="active")  # active, completed, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<MedicalRecord {self.id} for Patient {self.patient_id}>"


class Prescription(Base):
    """Prescription model"""
    __tablename__ = "prescriptions"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), index=True, nullable=False)
    medical_record_id = Column(String, ForeignKey("medical_records.id"), index=True)
    
    # Prescription details
    doctor_id = Column(String, index=True, nullable=False)
    hospital_id = Column(String, index=True)
    prescription_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Medication details
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration_days = Column(Integer)
    quantity = Column(Integer)
    
    # Instructions
    instructions = Column(Text)
    warnings = Column(Text)
    
    # Pharmacy information
    pharmacy_id = Column(String, index=True)
    dispensed_by = Column(String)
    dispensed_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String, default="pending")  # pending, dispensed, cancelled
    is_controlled_substance = Column(Boolean, default=False)
    
    # Refills
    refills_allowed = Column(Integer, default=0)
    refills_remaining = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Prescription {self.id} - {self.medication_name}>"


class Appointment(Base):
    """Appointment model"""
    __tablename__ = "appointments"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), index=True, nullable=False)
    
    # Appointment details
    doctor_id = Column(String, index=True, nullable=False)
    hospital_id = Column(String, index=True)
    department = Column(String, index=True)
    
    # Scheduling
    appointment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    
    # Type and reason
    appointment_type = Column(String)  # consultation, follow-up, procedure, etc.
    reason = Column(Text)
    notes = Column(Text)
    
    # Status
    status = Column(String, default="scheduled")  # scheduled, confirmed, completed, cancelled, no-show
    confirmed_at = Column(DateTime(timezone=True))
    
    # Reminders
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    
    def __repr__(self):
        return f"<Appointment {self.id} on {self.appointment_date}>"
