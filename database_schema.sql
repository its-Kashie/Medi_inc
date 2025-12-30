-- ========================================
-- COMPLETE HOSPITAL MANAGEMENT SYSTEM
-- PostgreSQL Database Schema
-- ========================================

-- Create Database
-- Run separately: CREATE DATABASE "HospitalManagementSystem";
-- Then connect: \c HospitalManagementSystem

-- ========================================
-- CORE TABLES
-- ========================================

-- Patients Table
CREATE TABLE Patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    contact_number VARCHAR(15),
    address VARCHAR(255),
    email VARCHAR(100),
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patient_name ON Patients (last_name, first_name);

-- Doctors Table
CREATE TABLE Doctors (
    doctor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    contact_number VARCHAR(15),
    email VARCHAR(100),
    available_schedule TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_specialty ON Doctors (specialty);

-- Departments Table
CREATE TABLE Departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(50),
    location VARCHAR(100)
);

-- Doctor_Department Junction Table
CREATE TABLE Doctor_Department (
    doctor_id INT,
    department_id INT,
    PRIMARY KEY (doctor_id, department_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES Departments(department_id) ON DELETE CASCADE
);

-- Staff Table
CREATE TABLE Staff (
    staff_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) NOT NULL CHECK (role IN ('Nurse', 'Worker', 'Admin', 'Pharmacist', 'Technician', 'Lab Assistant', 'Driver', 'Cleaner', 'Security')),
    department_id INT,
    contact_number VARCHAR(15),
    email VARCHAR(50),
    address TEXT,
    hire_date DATE,
    employment_status VARCHAR(20) DEFAULT 'Active' CHECK (employment_status IN ('Active', 'On Leave', 'Terminated')),
    FOREIGN KEY (department_id) REFERENCES Departments(department_id) ON DELETE SET NULL
);

CREATE INDEX idx_staff_role ON Staff (role);

-- Nurses Table
CREATE TABLE Nurses (
    nurse_id SERIAL PRIMARY KEY,
    staff_id INT NOT NULL,
    specialization VARCHAR(50),
    shift_hours TEXT,
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id) ON DELETE CASCADE
);

-- Workers Table
CREATE TABLE Workers (
    worker_id SERIAL PRIMARY KEY,
    staff_id INT,
    job_title VARCHAR(50),
    work_schedule TEXT,
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id) ON DELETE CASCADE
);

-- Visits Table (Master visit tracking)
CREATE TABLE Visits (
    visit_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT,
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    visit_type VARCHAR(50), -- Outpatient, Emergency, Follow-up
    chief_complaint TEXT,
    status VARCHAR(20) DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL
);

CREATE INDEX idx_visit_date ON Visits (visit_date, visit_time);

-- Appointments Table
CREATE TABLE Appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    purpose VARCHAR(255),
    status VARCHAR(20) DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL
);

CREATE INDEX idx_appointment_date ON Appointments (appointment_date, appointment_time);

-- Medical_Records Table
CREATE TABLE Medical_Records (
    record_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NULL,
    appointment_id INT NULL,
    diagnosis TEXT,
    treatment TEXT,
    prescription TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL,
    FOREIGN KEY (appointment_id) REFERENCES Appointments(appointment_id) ON DELETE NO ACTION
);

CREATE INDEX idx_record_patient ON Medical_Records (patient_id);

-- ========================================
-- SPECIALIZED DEPARTMENT TABLES
-- ========================================

-- 1. Non-Communicable Diseases (NCD)
CREATE TABLE NCD_Cases (
    ncd_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    condition_type VARCHAR(50), -- Diabetes, Hypertension, Asthma, Heart disease
    duration VARCHAR(20), -- Newly diagnosed, Chronic
    severity_level VARCHAR(20), -- Mild, Moderate, Severe
    current_control_status VARCHAR(20), -- Controlled, Uncontrolled
    lifestyle_factors TEXT, -- Smoking, obesity, inactivity
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Endocrinology
CREATE TABLE Endocrinology_Records (
    endo_record_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    suspected_disorder VARCHAR(100), -- Thyroid, PCOS, Adrenal
    confirmed_disorder VARCHAR(100),
    hormone_levels TEXT,
    treatment_phase VARCHAR(50), -- Observation, Medication
    follow_up_required BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Oncology
CREATE TABLE Oncology_Cases (
    oncology_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    suspected_cancer_type VARCHAR(100), -- Breast, Lung, Blood
    confirmed_cancer_type VARCHAR(100),
    cancer_stage VARCHAR(20), -- Stage I-IV
    treatment_plan TEXT, -- Chemo, Radio, Surgery
    case_status VARCHAR(20), -- Ongoing, Remission, Closed
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Pulmonology / Respiratory
CREATE TABLE Respiratory_Cases (
    respiratory_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    symptoms TEXT, -- Cough, breathlessness
    suspected_condition VARCHAR(100), -- TB, Asthma, COPD
    confirmed_condition VARCHAR(100),
    oxygen_level DECIMAL(5,2), -- SpO2 reading
    isolation_required BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Neurology
CREATE TABLE Neurology_Cases (
    neuro_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    presenting_symptoms TEXT, -- Seizure, headache
    suspected_disorder VARCHAR(100), -- Stroke, Epilepsy
    confirmed_disorder VARCHAR(100),
    functional_status VARCHAR(20), -- Mild, Moderate, Severe
    follow_up_plan TEXT, -- Rehab, Medication
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Orthopedics
CREATE TABLE Orthopedics_Cases (
    ortho_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    injury_type VARCHAR(50), -- Fracture, Pain
    injury_location VARCHAR(50), -- Knee, spine, arm
    injury_cause VARCHAR(100), -- Accident, Fall
    treatment_given TEXT, -- Cast, Surgery
    mobility_status VARCHAR(20), -- Normal, Restricted
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Pediatrics
CREATE TABLE Pediatrics_Cases (
    pediatric_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    child_age_months INT,
    growth_status VARCHAR(20), -- Normal, Delayed
    immunization_status VARCHAR(20), -- Complete, Pending
    illness_type VARCHAR(20), -- Acute, Chronic
    guardian_notes TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Emergency Department
CREATE TABLE Emergency_Cases (
    emergency_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    arrival_mode VARCHAR(20), -- Ambulance, Walk-in
    triage_level VARCHAR(10), -- Red, Yellow, Green
    chief_complaint TEXT,
    immediate_action TEXT, -- CPR, Stabilized
    outcome VARCHAR(20), -- Admitted, Referred, Discharged
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Surgery Department
CREATE TABLE Surgery_Cases (
    surgery_case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    surgery_type VARCHAR(20), -- Minor, Major
    surgery_name VARCHAR(100), -- Appendectomy
    surgery_date DATE,
    surgeon_id INT REFERENCES Doctors(doctor_id),
    surgeon_notes TEXT,
    recovery_status VARCHAR(20), -- Stable, Critical
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Maternity/OBGYN
CREATE TABLE Maternity_Cases (
    case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    pregnancy_week INT,
    risk_level VARCHAR(20), -- Low, Medium, High
    current_status VARCHAR(20), -- Ongoing, Delivered, Miscarriage
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Cardiology
CREATE TABLE Cardiology_Records (
    record_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    blood_pressure VARCHAR(20),
    cholesterol VARCHAR(20),
    ecg_result TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Mental Health
CREATE TABLE Mental_Health_Sessions (
    session_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    session_type VARCHAR(50), -- Therapy, Consultation, Crisis
    assessment TEXT,
    severity_level VARCHAR(20), -- Mild, Moderate, Severe
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Infectious Diseases
CREATE TABLE Infectious_Disease_Cases (
    case_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    suspected_disease VARCHAR(100),
    confirmed_disease VARCHAR(100),
    isolation_required BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Nutrition
CREATE TABLE Nutrition_Assessments (
    assessment_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    bmi DECIMAL(5,2),
    diet_plan TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- PHARMACY MODULE
-- ========================================

-- Medicine Master Table
CREATE TABLE Medicine (
    medicine_id SERIAL PRIMARY KEY,
    medicine_name VARCHAR(100) NOT NULL,
    medicine_type VARCHAR(20) CHECK (medicine_type IN ('Tablet', 'Syrup', 'Injection', 'Capsule', 'Ointment', 'Liquid')),
    strength VARCHAR(50), -- 250mg, 500mg
    manufacturer VARCHAR(100),
    batch_number VARCHAR(50),
    expiry_date DATE,
    unit_price DECIMAL(10,2),
    storage_condition VARCHAR(50), -- Normal, Cold storage
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Expired', 'Discontinued'))
);

CREATE INDEX idx_medicine_type ON Medicine (medicine_type);
CREATE INDEX idx_medicine_expiry ON Medicine (expiry_date);

-- Pharmacy Stock (Real-time inventory)
CREATE TABLE Pharmacy_Stock (
    stock_id SERIAL PRIMARY KEY,
    medicine_id INT REFERENCES Medicine(medicine_id),
    total_quantity INT CHECK (total_quantity >= 0),
    reserved_quantity INT DEFAULT 0,
    minimum_threshold INT DEFAULT 10,
    last_restocked DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pharmacy Issue/Dispense History
CREATE TABLE Pharmacy_Transactions (
    pharmacy_txn_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    medicine_id INT REFERENCES Medicine(medicine_id),
    quantity_issued INT,
    dosage_instruction TEXT, -- e.g. 1+1+1
    duration_days INT,
    prescribed_by INT REFERENCES Doctors(doctor_id),
    issued_by INT REFERENCES Staff(staff_id),
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pharmacy Return/Adjustment
CREATE TABLE Pharmacy_Returns (
    return_id SERIAL PRIMARY KEY,
    pharmacy_txn_id INT REFERENCES Pharmacy_Transactions(pharmacy_txn_id),
    quantity_returned INT,
    reason TEXT, -- Expired, Changed
    processed_by INT REFERENCES Staff(staff_id),
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prescriptions Detail Table
CREATE TABLE Prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES Patients(patient_id),
    doctor_id INT NOT NULL REFERENCES Doctors(doctor_id),
    visit_id INT REFERENCES Visits(visit_id),
    prescription_date DATE DEFAULT CURRENT_DATE,
    medication_name VARCHAR(100),
    dosage VARCHAR(100),
    frequency VARCHAR(50),
    duration VARCHAR(50),
    notes VARCHAR(255)
);

-- Medical_Records_Medicine Junction Table
CREATE TABLE Medical_Records_Medicine (
    record_id INT REFERENCES Medical_Records(record_id) ON DELETE CASCADE,
    medicine_id INT REFERENCES Medicine(medicine_id) ON DELETE CASCADE,
    dosage VARCHAR(50),
    PRIMARY KEY (record_id, medicine_id)
);

-- ========================================
-- CLEANING / HOUSEKEEPING MODULE
-- ========================================

-- Cleaning Staff (subset of Staff table, but can have specialized tracking)
CREATE TABLE Cleaning_Staff (
    cleaner_id SERIAL PRIMARY KEY,
    staff_id INT REFERENCES Staff(staff_id) ON DELETE CASCADE,
    shift VARCHAR(20), -- Morning, Evening, Night
    assigned_zone VARCHAR(50), -- ICU, Ward
    employment_status VARCHAR(20) DEFAULT 'Active'
);

-- Cleaning Task Log
CREATE TABLE Cleaning_Tasks (
    cleaning_task_id SERIAL PRIMARY KEY,
    room_id INT, -- Will be linked after Rooms table
    cleaning_type VARCHAR(20), -- Routine, Deep, Emergency
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    cleaned_by INT REFERENCES Staff(staff_id),
    supervisor_verified BOOLEAN DEFAULT FALSE,
    remarks TEXT
);

-- Infection Control Cleaning
CREATE TABLE Infection_Control_Cleaning (
    infection_clean_id SERIAL PRIMARY KEY,
    room_id INT, -- Linked after Rooms
    infection_type VARCHAR(50), -- COVID, TB
    disinfectant_used VARCHAR(100),
    protective_gear_used TEXT,
    cleaned_by INT REFERENCES Staff(staff_id),
    clearance_status VARCHAR(20), -- Cleared, Pending
    cleared_at TIMESTAMP
);

-- ========================================
-- AMBULANCE MODULE
-- ========================================

-- Ambulance Master
CREATE TABLE Ambulance (
    ambulance_id SERIAL PRIMARY KEY,
    vehicle_number VARCHAR(20) UNIQUE,
    ambulance_type VARCHAR(20), -- Basic, ICU
    current_status VARCHAR(20) CHECK (current_status IN ('Available', 'Busy', 'Maintenance')),
    last_service_date DATE,
    assigned_driver INT REFERENCES Staff(staff_id) ON DELETE SET NULL
);

-- Ambulance Driver
CREATE TABLE Ambulance_Drivers (
    driver_id SERIAL PRIMARY KEY,
    staff_id INT REFERENCES Staff(staff_id) ON DELETE CASCADE,
    license_number VARCHAR(50),
    shift VARCHAR(20), -- Day, Night
    status VARCHAR(20) DEFAULT 'Active' -- Active, Off duty
);

-- Ambulance Trip Log
CREATE TABLE Ambulance_Trips (
    trip_id SERIAL PRIMARY KEY,
    ambulance_id INT REFERENCES Ambulance(ambulance_id),
    visit_id INT REFERENCES Visits(visit_id),
    patient_id INT REFERENCES Patients(patient_id),
    pickup_location VARCHAR(255),
    dropoff_location VARCHAR(255),
    emergency_type VARCHAR(50), -- Trauma, Maternity
    trip_start_time TIMESTAMP,
    trip_end_time TIMESTAMP,
    trip_status VARCHAR(20) CHECK (trip_status IN ('Completed', 'Cancelled', 'In Progress'))
);

CREATE INDEX idx_trip_status ON Ambulance_Trips (trip_status);

-- ========================================
-- ROOMS & FACILITIES
-- ========================================

-- Room Types
CREATE TABLE Room_Types (
    room_type_id SERIAL PRIMARY KEY,
    room_type_name VARCHAR(50) NOT NULL, -- ICU, Laboratory, Cosmetic, Operating, Staff
    description VARCHAR(255)
);

-- Rooms
CREATE TABLE Rooms (
    room_id SERIAL PRIMARY KEY,
    room_number VARCHAR(10) UNIQUE NOT NULL,
    room_type_id INT REFERENCES Room_Types(room_type_id) ON DELETE SET NULL,
    capacity INT,
    status VARCHAR(20) CHECK (status IN ('Available', 'Occupied', 'Under Maintenance')),
    last_serviced DATE
);

-- Room Assignments
CREATE TABLE Room_Assignments (
    assignment_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES Rooms(room_id) ON DELETE CASCADE,
    staff_id INT NULL REFERENCES Staff(staff_id) ON DELETE SET NULL,
    patient_id INT NULL REFERENCES Patients(patient_id) ON DELETE SET NULL,
    assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL
);

-- Add Foreign Keys to Cleaning Tables
ALTER TABLE Cleaning_Tasks ADD FOREIGN KEY (room_id) REFERENCES Rooms(room_id);
ALTER TABLE Infection_Control_Cleaning ADD FOREIGN KEY (room_id) REFERENCES Rooms(room_id);

-- Cleaning Service (Historical log)
CREATE TABLE Cleaning_Service (
    service_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES Rooms(room_id),
    service_date DATE DEFAULT CURRENT_DATE,
    service_time TIME DEFAULT CURRENT_TIME,
    staff_id INT REFERENCES Staff(staff_id),
    notes VARCHAR(255)
);

-- ========================================
-- BILLING & FINANCE
-- ========================================

CREATE TABLE Billing (
    bill_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES Patients(patient_id) ON DELETE CASCADE,
    appointment_id INT REFERENCES Appointments(appointment_id) ON DELETE NO ACTION,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'Pending',
    payment_date DATE,
    insurance_provider VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payment_status ON Billing (payment_status);

-- ========================================
-- BLOOD BANK
-- ========================================

CREATE TABLE Blood_Bank (
    blood_id SERIAL PRIMARY KEY,
    blood_type VARCHAR(3) CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    stock_quantity INT CHECK (stock_quantity >= 0),
    last_updated DATE
);

CREATE INDEX idx_blood_type ON Blood_Bank (blood_type);

-- ========================================
-- WASTE MANAGEMENT
-- ========================================

CREATE TABLE Waste_Logs (
    log_id SERIAL PRIMARY KEY,
    waste_type VARCHAR(50), -- Medical, General, Hazardous
    weight_kg DECIMAL(5,2),
    source_location VARCHAR(100),
    disposal_company VARCHAR(100),
    cost DECIMAL(10,2),
    pickup_time TIMESTAMP,
    compliance_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- SAMPLE DATA INSERTION
-- ========================================

-- Insert Departments
INSERT INTO Departments (department_name, location) VALUES
('Cardiology', '2nd Floor'),
('Neurology', '3rd Floor'),
('Orthopedics', '4th Floor'),
('Dermatology', '1st Floor'),
('Pediatrics', '2nd Floor'),
('General Surgery', '5th Floor'),
('Gynecology', '3rd Floor'),
('Psychiatry', '6th Floor'),
('Ophthalmology', '4th Floor'),
('ENT', '1st Floor'),
('Emergency', 'Ground Floor'),
('Oncology', '5th Floor');

-- Insert Sample Patients
INSERT INTO Patients (first_name, last_name, date_of_birth, gender, contact_number, address, email, medical_history) VALUES
('John', 'Doe', '1985-05-15', 'M', '555-1234', '123 Elm St, Springfield', 'john.doe@email.com', 'Hypertension'),
('Jane', 'Smith', '1992-08-22', 'F', '555-5678', '456 Oak St, Springfield', 'jane.smith@email.com', 'Asthma'),
('Michael', 'Johnson', '1975-02-10', 'M', '555-8765', '789 Pine St, Springfield', 'michael.johnson@email.com', 'Diabetes'),
('Emily', 'Davis', '2000-11-30', 'F', '555-4321', '321 Birch St, Springfield', 'emily.davis@email.com', 'None'),
('Daniel', 'Brown', '1990-03-25', 'M', '555-6543', '654 Maple St, Springfield', 'daniel.brown@email.com', 'Migraine');

-- Insert Sample Doctors
INSERT INTO Doctors (first_name, last_name, specialty, contact_number, email, available_schedule) VALUES
('Dr. Alice', 'Miller', 'Cardiology', '555-1122', 'alice.miller@email.com', 'Mon-Wed 9AM-5PM'),
('Dr. Bob', 'Williams', 'Neurology', '555-2233', 'bob.williams@email.com', 'Tue-Thu 10AM-6PM'),
('Dr. Charlie', 'Brown', 'Orthopedics', '555-3344', 'charlie.brown@email.com', 'Mon-Fri 8AM-4PM'),
('Dr. Diana', 'Jones', 'Dermatology', '555-4455', 'diana.jones@email.com', 'Mon-Fri 9AM-5PM'),
('Dr. Eva', 'Garcia', 'Pediatrics', '555-5566', 'eva.garcia@email.com', 'Wed-Fri 10AM-6PM');

-- Insert Doctor-Department Links
INSERT INTO Doctor_Department (doctor_id, department_id) VALUES
(1, 1), (2, 2), (3, 3), (4, 4), (5, 5);

-- Insert Sample Staff
INSERT INTO Staff (first_name, last_name, role, department_id, contact_number, email, address, hire_date) VALUES
('Alice', 'Johnson', 'Nurse', 1, '555-0100', 'alice.j@hospital.com', '123 Elm St', '2023-08-01'),
('Bob', 'Smith', 'Technician', 2, '555-0101', 'bob.s@hospital.com', '456 Oak St', '2022-07-15'),
('Charlie', 'Davis', 'Driver', 11, '555-0102', 'charlie.d@hospital.com', '789 Pine St', '2021-09-10'),
('David', 'Lee', 'Pharmacist', 1, '555-0103', 'david.l@hospital.com', '321 Maple St', '2020-12-05'),
('Eva', 'Wilson', 'Cleaner', 1, '555-0104', 'eva.w@hospital.com', '654 Birch St', '2024-03-20');

-- Insert Room Types
INSERT INTO Room_Types (room_type_name, description) VALUES
('ICU', 'Intensive Care Unit for critical patients'),
('Laboratory', 'Medical testing and diagnostics'),
('Operating', 'Operating rooms for surgeries'),
('Ward', 'General patient ward'),
('Emergency', 'Emergency treatment rooms');

-- Insert Sample Rooms
INSERT INTO Rooms (room_number, room_type_id, capacity, status, last_serviced) VALUES
('ICU-101', 1, 2, 'Available', '2024-12-01'),
('LAB-201', 2, 4, 'Available', '2024-12-01'),
('OPR-301', 3, 2, 'Available', '2024-12-01'),
('WARD-401', 4, 6, 'Occupied', '2024-11-30'),
('ER-101', 5, 3, 'Available', '2024-12-01');

-- Insert Sample Medicine
INSERT INTO Medicine (medicine_name, medicine_type, strength, manufacturer, batch_number, expiry_date, unit_price, storage_condition, status) VALUES
('Paracetamol', 'Tablet', '500mg', 'PharmaCo', 'BATCH001', '2025-12-31', 5.00, 'Normal', 'Active'),
('Amoxicillin', 'Capsule', '250mg', 'MediCorp', 'BATCH002', '2025-06-30', 12.00, 'Normal', 'Active'),
('Insulin', 'Injection', '100IU', 'DiabetesCare', 'BATCH003', '2025-03-31', 45.00, 'Cold storage', 'Active'),
('Aspirin', 'Tablet', '75mg', 'CardioMed', 'BATCH004', '2026-01-31', 3.50, 'Normal', 'Active'),
('Ibuprofen', 'Tablet', '400mg', 'PainRelief Inc', 'BATCH005', '2025-11-30', 8.00, 'Normal', 'Active');

-- Insert Pharmacy Stock
INSERT INTO Pharmacy_Stock (medicine_id, total_quantity, reserved_quantity, minimum_threshold) VALUES
(1, 500, 0, 100),
(2, 300, 0, 50),
(3, 150, 0, 20),
(4, 400, 0, 80),
(5, 350, 0, 70);

-- Insert Blood Bank Data
INSERT INTO Blood_Bank (blood_type, stock_quantity, last_updated) VALUES
('A+', 25, '2024-12-20'),
('A-', 15, '2024-12-20'),
('B+', 30, '2024-12-19'),
('B-', 10, '2024-12-18'),
('O+', 50, '2024-12-21'),
('O-', 35, '2024-12-21'),
('AB+', 20, '2024-12-17'),
('AB-', 8, '2024-12-16');

-- Insert Sample Ambulance
INSERT INTO Ambulance (vehicle_number, ambulance_type, current_status, last_service_date, assigned_driver) VALUES
('AMB-001', 'ICU', 'Available', '2024-11-15', 3),
('AMB-002', 'Basic', 'Available', '2024-11-20', NULL),
('AMB-003', 'ICU', 'Maintenance', '2024-10-30', NULL);

-- ========================================
-- VIEWS FOR COMMON QUERIES
-- ========================================

-- Active Patients View
CREATE VIEW vw_active_patients AS
SELECT 
    p.patient_id,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.date_of_birth,
    p.gender,
    p.contact_number,
    p.email
FROM Patients p;

-- Doctor Schedule View
CREATE VIEW vw_doctor_schedule AS
SELECT 
    d.doctor_id,
    d.first_name || ' ' || d.last_name AS doctor_name,
    d.specialty,
    d.available_schedule,
    dep.department_name
FROM Doctors d
JOIN Doctor_Department dd ON d.doctor_id = dd.doctor_id
JOIN Departments dep ON dd.department_id = dep.department_id;

-- Pharmacy Stock Alert View
CREATE VIEW vw_low_stock_medicines AS
SELECT 
    m.medicine_id,
    m.medicine_name,
    m.medicine_type,
    m.strength,
    ps.total_quantity,
    ps.minimum_threshold
FROM Medicine m
JOIN Pharmacy_Stock ps ON m.medicine_id = ps.medicine_id
WHERE ps.total_quantity <= ps.minimum_threshold;

-- Available Rooms View
CREATE VIEW vw_available_rooms AS
SELECT 
    r.room_id,
    r.room_number,
    rt.room_type_name,
    r.capacity,
    r.status
FROM Rooms r
JOIN Room_Types rt ON r.room_type_id = rt.room_type_id
WHERE r.status = 'Available';

-- ========================================
-- END OF SCHEMA
-- ========================================

-- Display success message
SELECT 'Hospital Management System Database Created Successfully!' AS status;