# Agent Roles & Responsibilities

**Version**: 1.0  
**Last Updated**: December 2025  
**Document Type**: Technical Reference

---

## Table of Contents

1. [Agent Architecture Overview](#agent-architecture-overview)
2. [Operational Agents (Backend Core)](#operational-agents-backend-core)
3. [Orchestrator Agents (Backend Reporting)](#orchestrator-agents-backend-reporting)
4. [Agent Communication Protocols](#agent-communication-protocols)
5. [Agent Lifecycle Management](#agent-lifecycle-management)
6. [Error Handling & Recovery](#error-handling--recovery)

---

## Agent Architecture Overview

HealthLink360 employs **14 specialized AI agents** organized into three functional tiers:

```
┌─────────────────────────────────────────────────────────────┐
│                    TIER 3: ORCHESTRATORS                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Hospital    │  │  NIH Agent   │  │  R&D Agent   │      │
│  │   Central    │  │              │  │              │      │
│  │    Agent     │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│                  TIER 2: DEPARTMENT AGENTS                   │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │Cardio- │ │Maternal│ │Infect. │ │Nutri-  │ │Mental  │   │
│  │logy    │ │Health  │ │Disease │ │tion    │ │Health  │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐                          │
│  │  NCD   │ │Endo-   │ │Onco-   │                          │
│  │        │ │crinol. │ │logy    │                          │
│  └────────┘ └────────┘ └────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│                 TIER 1: OPERATIONAL AGENTS                   │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │Tracking│ │Maternal│ │Mental  │ │Pharmacy│ │Criminal│   │
│  │(Emerg.)│ │Health  │ │Health  │ │        │ │Case    │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                              │
│  ┌────────┐                                                 │
│  │ Waste  │                                                 │
│  │  Mgmt  │                                                 │
│  └────────┘                                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Tiers

**Tier 1: Operational Agents**
- **Purpose**: Real-time patient care and service delivery
- **Backend**: Backend Core
- **Latency**: <500ms
- **Database**: PostgreSQL (transactional)
- **MCP**: Core Agents MCP

**Tier 2: Department Agents**
- **Purpose**: Data aggregation and departmental analytics
- **Backend**: Backend Reporting
- **Latency**: <5s
- **Database**: MongoDB (analytical)
- **MCP**: Report Generation MCP, Orchestrator MCP

**Tier 3: Orchestrator Agents**
- **Purpose**: Multi-agent coordination and national-level decision making
- **Backend**: Backend Reporting
- **Latency**: <30s
- **Database**: MongoDB (aggregated data)
- **MCP**: NIH MCP, Orchestrator MCP, R&D MCP

---

## Operational Agents (Backend Core)

### 1. Tracking Agent (Emergency & Ambulance)

**Agent ID**: `tracking_agent_001`  
**Backend**: Backend Core  
**MCP Server**: Core Agents MCP

#### Purpose

Coordinate real-time emergency response, ambulance dispatch, and critical patient tracking across the healthcare network.

#### Responsibilities

1. **Emergency Call Management**
   - Receive and triage emergency calls
   - Assess severity using standardized protocols (e.g., Emergency Severity Index)
   - Dispatch appropriate resources

2. **Ambulance Coordination**
   - Track ambulance locations via GPS
   - Optimize routing based on traffic and distance
   - Coordinate with receiving hospitals for bed availability

3. **Patient Handoff**
   - Facilitate seamless handoff between ambulance and emergency department
   - Ensure continuity of care documentation
   - Alert specialist teams for critical cases

4. **Resource Monitoring**
   - Track emergency department bed availability
   - Monitor critical care equipment status
   - Coordinate inter-hospital transfers for specialized care

#### Data Handled

```python
emergency_case = {
    "case_id": "EMG-2025-001234",
    "patient_id": "P12345",  # Encrypted
    "call_timestamp": "2025-03-15T14:23:00Z",
    "severity": "critical",  # critical, urgent, non-urgent
    "chief_complaint": "Chest pain",
    "location": {
        "latitude": 33.6844,
        "longitude": 73.0479
    },
    "ambulance_assigned": "AMB-001",
    "ambulance_dispatch_time": "2025-03-15T14:24:30Z",
    "estimated_arrival_time": "2025-03-15T14:36:00Z",
    "receiving_hospital": "H001",
    "bed_reserved": "ER-BED-12",
    "specialist_alerted": ["cardiology"],
    "vitals_enroute": {
        "heart_rate": 110,
        "blood_pressure": "160/95",
        "oxygen_saturation": 92
    }
}
```

#### Security Considerations

- **End-to-End Encryption**: All patient data encrypted in transit
- **Access Control**: Only authorized emergency personnel can access case details
- **Audit Logging**: All emergency dispatches logged with timestamps
- **HIPAA Compliance**: PHI protected according to emergency care regulations

#### Decision-Making Logic

```python
def dispatch_ambulance(emergency_call):
    """Intelligent ambulance dispatch"""
    
    # 1. Assess severity
    severity = assess_severity(emergency_call)
    
    # 2. Find nearest available ambulance
    ambulance = find_nearest_ambulance(emergency_call.location)
    
    # 3. Check receiving hospital capacity
    hospital = find_hospital_with_capacity(
        location=emergency_call.location,
        required_specialty=emergency_call.chief_complaint
    )
    
    # 4. Reserve bed and alert specialists
    if severity == "critical":
        reserve_bed(hospital, bed_type="ICU")
        alert_specialists(hospital, emergency_call.chief_complaint)
    
    # 5. Dispatch ambulance with optimal route
    route = calculate_optimal_route(
        ambulance.location,
        emergency_call.location,
        hospital.location
    )
    
    # 6. Notify all stakeholders
    notify_ambulance_crew(ambulance, emergency_call, route)
    notify_hospital(hospital, emergency_call, estimated_arrival)
    
    return {
        "ambulance_id": ambulance.id,
        "hospital_id": hospital.id,
        "estimated_arrival": estimated_arrival
    }
```

#### Performance Metrics

- **Dispatch Time**: <2 minutes from call receipt
- **Ambulance Arrival**: <15 minutes (urban), <30 minutes (rural)
- **Handoff Time**: <5 minutes from ambulance arrival to ER admission
- **Uptime**: 99.99% (critical system)

---

### 2. Maternal Health Agent (Operational)

**Agent ID**: `maternal_health_ops_agent_001`  
**Backend**: Backend Core  
**MCP Server**: Core Agents MCP

#### Purpose

Manage real-time maternal health services including antenatal care, delivery coordination, and postnatal follow-up.

#### Responsibilities

1. **Pregnancy Registration & Tracking**
   - Register new pregnancies
   - Schedule antenatal care (ANC) visits
   - Track pregnancy milestones

2. **High-Risk Pregnancy Management**
   - Identify high-risk pregnancies (age, comorbidities, previous complications)
   - Escalate to specialist obstetricians
   - Coordinate additional monitoring (ultrasounds, fetal monitoring)

3. **Delivery Coordination**
   - Schedule planned deliveries
   - Coordinate emergency cesarean sections
   - Ensure NICU availability for high-risk deliveries

4. **Postnatal Care**
   - Schedule postnatal visits
   - Monitor for postpartum complications
   - Coordinate breastfeeding support

#### Data Handled

```python
maternal_record = {
    "patient_id": "P67890",  # Encrypted
    "pregnancy_id": "PREG-2025-5678",
    "registration_date": "2025-01-10",
    "estimated_due_date": "2025-09-15",
    "gestational_age": 12,  # weeks
    "risk_level": "high",  # low, medium, high
    "risk_factors": [
        "Advanced maternal age (38 years)",
        "Previous cesarean section",
        "Gestational diabetes"
    ],
    "anc_visits": [
        {
            "visit_number": 1,
            "date": "2025-01-10",
            "weight": 65,  # kg
            "blood_pressure": "120/80",
            "fundal_height": 12,  # cm
            "fetal_heart_rate": 145
        }
    ],
    "scheduled_delivery": {
        "date": "2025-09-10",
        "method": "planned_cesarean",
        "surgeon": "DR-OB-001",
        "or_reserved": "OR-3"
    }
}
```

#### Security Considerations

- **HIPAA Compliance**: Maternal health records are highly sensitive PHI
- **Restricted Access**: Only OB/GYN personnel and assigned nurses
- **Audit Logging**: All access to maternal records logged
- **Consent Management**: Patient consent for data sharing with specialists

#### Decision-Making Logic

```python
def assess_pregnancy_risk(maternal_record):
    """Risk stratification for pregnant patients"""
    
    risk_score = 0
    risk_factors = []
    
    # Age-based risk
    if maternal_record.age < 18 or maternal_record.age > 35:
        risk_score += 2
        risk_factors.append("Age-related risk")
    
    # Parity-based risk
    if maternal_record.parity == 0:  # First pregnancy
        risk_score += 1
    elif maternal_record.parity > 4:  # Grand multiparity
        risk_score += 2
        risk_factors.append("Grand multiparity")
    
    # Medical history
    if "previous_cesarean" in maternal_record.history:
        risk_score += 2
        risk_factors.append("Previous cesarean section")
    
    if "gestational_diabetes" in maternal_record.current_conditions:
        risk_score += 3
        risk_factors.append("Gestational diabetes")
    
    if "preeclampsia" in maternal_record.current_conditions:
        risk_score += 4
        risk_factors.append("Preeclampsia")
    
    # Determine risk level
    if risk_score >= 5:
        risk_level = "high"
        # Escalate to specialist
        escalate_to_specialist(maternal_record, risk_factors)
    elif risk_score >= 3:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_factors": risk_factors
    }
```

---

### 3. Mental Health Agent (Operational)

**Agent ID**: `mental_health_ops_agent_001`  
**Backend**: Backend Core  
**MCP Server**: Core Agents MCP

#### Purpose

Provide mental health service coordination with enhanced confidentiality and crisis intervention capabilities.

#### Responsibilities

1. **Patient Assessment**
   - Conduct initial psychiatric evaluations
   - Administer standardized assessment tools (PHQ-9, GAD-7)
   - Risk assessment for self-harm and suicide

2. **Treatment Coordination**
   - Schedule therapy sessions
   - Coordinate medication management
   - Track treatment adherence

3. **Crisis Intervention**
   - 24/7 crisis hotline integration
   - Emergency psychiatric evaluations
   - Involuntary commitment coordination (when legally required)

4. **Confidentiality Management**
   - Enhanced privacy controls beyond standard HIPAA
   - Separate consent for data sharing
   - Stigma-sensitive communication

#### Data Handled

```python
mental_health_session = {
    "session_id": "MH-SESSION-2025-9876",
    "patient_id": "P11111",  # Encrypted
    "session_date": "2025-03-15",
    "session_type": "individual_therapy",  # individual, group, family
    "therapist_id": "DR-PSY-005",
    "duration_minutes": 50,
    
    # Clinical notes (encrypted at rest)
    "clinical_notes_encrypted": "...",
    
    # Structured data for reporting (de-identified)
    "diagnosis": "F32.1",  # ICD-10: Major depressive disorder, moderate
    "treatment_modality": "CBT",  # Cognitive Behavioral Therapy
    "symptom_severity": {
        "phq9_score": 15,  # Moderate depression
        "gad7_score": 12   # Moderate anxiety
    },
    "suicide_risk": "low",  # low, medium, high, imminent
    "medications": [
        {
            "name": "Sertraline",
            "dosage": "50mg",
            "frequency": "once daily"
        }
    ]
}
```

#### Security Considerations

- **Enhanced Encryption**: Mental health notes encrypted with separate key
- **Restricted Access**: Only assigned therapist and supervising psychiatrist
- **Separate Database**: Mental health data in isolated database partition
- **Audit Logging**: All access logged and reviewed monthly
- **Legal Protections**: Compliance with mental health confidentiality laws

#### Crisis Intervention Protocol

```python
def assess_suicide_risk(patient_assessment):
    """Suicide risk assessment and intervention"""
    
    risk_factors = []
    protective_factors = []
    
    # Risk factors
    if patient_assessment.previous_attempts:
        risk_factors.append("Previous suicide attempts")
    
    if patient_assessment.current_ideation:
        risk_factors.append("Current suicidal ideation")
    
    if patient_assessment.has_plan:
        risk_factors.append("Has suicide plan")
    
    if patient_assessment.access_to_means:
        risk_factors.append("Access to lethal means")
    
    if patient_assessment.substance_abuse:
        risk_factors.append("Substance abuse")
    
    # Protective factors
    if patient_assessment.social_support:
        protective_factors.append("Strong social support")
    
    if patient_assessment.treatment_engagement:
        protective_factors.append("Engaged in treatment")
    
    # Determine risk level
    if len(risk_factors) >= 3 and patient_assessment.has_plan:
        risk_level = "imminent"
        # Immediate intervention
        initiate_emergency_protocol(patient_assessment)
        notify_crisis_team()
        consider_involuntary_admission()
    elif len(risk_factors) >= 2:
        risk_level = "high"
        # Enhanced monitoring
        increase_session_frequency()
        notify_emergency_contact()
        safety_planning()
    else:
        risk_level = "low"
        # Standard care
        continue_treatment_plan()
    
    return {
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "protective_factors": protective_factors,
        "intervention_plan": generate_intervention_plan(risk_level)
    }
```

---

### 4. Pharmacy Agent

**Agent ID**: `pharmacy_agent_001`  
**Backend**: Backend Core  
**MCP Server**: Core Agents MCP

#### Purpose

Manage medication dispensing, inventory control, and drug interaction checking.

#### Responsibilities

1. **Prescription Processing**
   - Validate prescriptions (authenticity, dosage, interactions)
   - Dispense medications
   - Provide patient counseling

2. **Inventory Management**
   - Track medication stock levels
   - Automated reordering for low stock
   - Expiry date monitoring

3. **Drug Interaction Checking**
   - Screen for drug-drug interactions
   - Screen for drug-allergy interactions
   - Dosage validation based on patient factors (age, weight, renal function)

4. **Controlled Substance Monitoring**
   - Track controlled substance dispensing
   - Identify potential prescription drug abuse
   - Regulatory compliance reporting

#### Data Handled

```python
prescription = {
    "prescription_id": "RX-2025-12345",
    "patient_id": "P22222",  # Encrypted
    "prescriber_id": "DR-001",
    "prescription_date": "2025-03-15",
    "medications": [
        {
            "drug_name": "Metformin",
            "generic_name": "Metformin HCl",
            "dosage": "500mg",
            "frequency": "twice daily",
            "duration_days": 30,
            "quantity": 60,
            "refills": 2
        }
    ],
    "dispensing_pharmacist": "PHARM-005",
    "dispensed_date": "2025-03-15T10:30:00Z",
    "patient_counseling_provided": true,
    "interaction_check": {
        "drug_drug_interactions": [],
        "drug_allergy_interactions": [],
        "warnings": ["Take with food to reduce GI upset"]
    }
}
```

#### Drug Interaction Checking

```python
def check_drug_interactions(new_medication, patient_medications, patient_allergies):
    """Comprehensive drug interaction screening"""
    
    interactions = []
    warnings = []
    
    # Check drug-drug interactions
    for existing_med in patient_medications:
        interaction = drug_interaction_database.check(
            new_medication,
            existing_med
        )
        if interaction:
            interactions.append({
                "type": "drug-drug",
                "severity": interaction.severity,  # minor, moderate, severe
                "description": interaction.description,
                "recommendation": interaction.recommendation
            })
    
    # Check drug-allergy interactions
    for allergy in patient_allergies:
        if is_cross_reactive(new_medication, allergy):
            interactions.append({
                "type": "drug-allergy",
                "severity": "severe",
                "description": f"Cross-reactivity with {allergy}",
                "recommendation": "Do not dispense - contact prescriber"
            })
    
    # Check dosage appropriateness
    if patient.age > 65:
        if new_medication in beers_criteria_drugs:
            warnings.append("Potentially inappropriate for elderly patients")
    
    if patient.renal_function < 30:  # CrCl < 30 mL/min
        if new_medication.requires_renal_adjustment:
            warnings.append("Dosage adjustment required for renal impairment")
    
    # Severe interactions require pharmacist intervention
    severe_interactions = [i for i in interactions if i["severity"] == "severe"]
    if severe_interactions:
        alert_pharmacist(prescription, severe_interactions)
        contact_prescriber(prescription, severe_interactions)
    
    return {
        "interactions": interactions,
        "warnings": warnings,
        "safe_to_dispense": len(severe_interactions) == 0
    }
```

#### Controlled Substance Monitoring

```python
def monitor_controlled_substances(patient_id, new_prescription):
    """Detect potential prescription drug abuse"""
    
    # Get patient's controlled substance history (last 6 months)
    history = get_controlled_substance_history(patient_id, months=6)
    
    red_flags = []
    
    # Check for early refills
    if new_prescription.is_controlled_substance:
        last_fill = get_last_fill(patient_id, new_prescription.drug_name)
        if last_fill:
            days_since_last_fill = (today - last_fill.date).days
            expected_duration = last_fill.duration_days
            
            if days_since_last_fill < expected_duration * 0.75:
                red_flags.append("Early refill request")
    
    # Check for multiple prescribers
    prescribers = set([rx.prescriber_id for rx in history])
    if len(prescribers) > 3:
        red_flags.append("Multiple prescribers for controlled substances")
    
    # Check for multiple pharmacies
    pharmacies = set([rx.pharmacy_id for rx in history])
    if len(pharmacies) > 2:
        red_flags.append("Multiple pharmacies used")
    
    # Check for high morphine equivalent dose (opioids)
    if new_prescription.drug_class == "opioid":
        total_med = calculate_morphine_equivalent_dose(history + [new_prescription])
        if total_med > 90:  # CDC guideline threshold
            red_flags.append(f"High morphine equivalent dose: {total_med} mg/day")
    
    # Alert if red flags present
    if red_flags:
        alert_pharmacist_in_charge(patient_id, new_prescription, red_flags)
        report_to_prescription_monitoring_program(patient_id, red_flags)
    
    return {
        "red_flags": red_flags,
        "requires_review": len(red_flags) > 0
    }
```

---

### 5. Criminal Case Agent

**Agent ID**: `criminal_case_agent_001`  
**Backend**: Backend Core (Isolated Database)  
**MCP Server**: Core Agents MCP

#### Purpose

Manage medico-legal cases with strict chain of custody and evidence integrity.

#### Responsibilities

1. **Forensic Evidence Collection**
   - Document injuries and medical findings
   - Collect biological samples (blood, DNA)
   - Photograph evidence

2. **Chain of Custody**
   - Maintain tamper-proof evidence logs
   - Track evidence transfers
   - Cryptographic signatures on all entries

3. **Law Enforcement Coordination**
   - Secure communication with police
   - Court report generation
   - Expert witness coordination

4. **Victim Support**
   - Coordinate with victim support services
   - Ensure privacy and dignity
   - Trauma-informed care

#### Data Handled

```python
criminal_case = {
    "case_id": "MEDICO-LEGAL-2025-0123",
    "case_number": "FIR-2025-5678",  # Police case number
    "patient_id": "P33333",  # Encrypted
    "case_type": "assault",  # assault, sexual_assault, homicide, suspicious_death
    "admission_date": "2025-03-15T18:45:00Z",
    "reporting_officer": "OFFICER-001",
    "forensic_examiner": "DR-FORENSIC-002",
    
    "medical_findings": {
        "injuries": [
            {
                "location": "Right forearm",
                "type": "Laceration",
                "size": "5cm x 1cm",
                "depth": "Superficial",
                "photograph_id": "IMG-001"
            }
        ],
        "medical_opinion": "Injuries consistent with defensive wounds"
    },
    
    "evidence_collected": [
        {
            "evidence_id": "EVID-001",
            "type": "Blood sample",
            "collection_time": "2025-03-15T19:00:00Z",
            "collected_by": "DR-FORENSIC-002",
            "sealed_by": "DR-FORENSIC-002",
            "seal_number": "SEAL-12345",
            "cryptographic_hash": "sha256:abcd1234..."
        }
    ],
    
    "chain_of_custody": [
        {
            "timestamp": "2025-03-15T19:00:00Z",
            "action": "Collected",
            "person": "DR-FORENSIC-002",
            "signature": "digital_signature_hash"
        },
        {
            "timestamp": "2025-03-15T19:30:00Z",
            "action": "Transferred to police",
            "person": "OFFICER-001",
            "signature": "digital_signature_hash"
        }
    ]
}
```

#### Security Considerations

- **Isolated Database**: Criminal cases in completely separate database
- **Access Control**: Restricted to forensic personnel and authorized law enforcement
- **Tamper-Proof Logging**: Blockchain-style immutable audit trail
- **Legal Compliance**: Compliance with criminal procedure codes
- **Evidence Integrity**: Cryptographic hashing of all evidence entries

#### Chain of Custody Protocol

```python
def transfer_evidence(evidence_id, from_person, to_person, reason):
    """Maintain tamper-proof chain of custody"""
    
    # Verify current custodian
    current_custody = get_current_custodian(evidence_id)
    if current_custody != from_person:
        raise ChainOfCustodyViolation("Unauthorized transfer attempt")
    
    # Create transfer record
    transfer_record = {
        "evidence_id": evidence_id,
        "timestamp": datetime.utcnow(),
        "from_person": from_person,
        "to_person": to_person,
        "reason": reason,
        "witness": get_witness(),  # Transfers require witness
        "location": get_current_location()
    }
    
    # Generate cryptographic signature
    transfer_hash = generate_hash(transfer_record)
    transfer_record["signature"] = sign_with_private_key(transfer_hash)
    
    # Append to immutable log
    append_to_chain_of_custody(evidence_id, transfer_record)
    
    # Verify integrity of entire chain
    verify_chain_integrity(evidence_id)
    
    # Notify all stakeholders
    notify_case_officer(evidence_id, transfer_record)
    log_to_audit_trail(transfer_record)
    
    return transfer_record
```

---

### 6. Waste Management Agent

**Agent ID**: `waste_management_agent_001`  
**Backend**: Backend Core  
**MCP Server**: Core Agents MCP

#### Purpose

Track medical waste from generation to disposal, ensuring regulatory compliance and environmental safety.

#### Responsibilities

1. **Waste Categorization**
   - Infectious waste
   - Hazardous waste (chemicals, pharmaceuticals)
   - Radioactive waste
   - General waste

2. **Disposal Scheduling**
   - Coordinate waste pickup
   - Track disposal to authorized facilities
   - Maintain disposal manifests

3. **Regulatory Compliance**
   - Ensure compliance with environmental regulations
   - Generate compliance reports
   - Track certifications of disposal facilities

4. **Environmental Impact Reporting**
   - Calculate carbon footprint
   - Track waste reduction initiatives
   - Report to environmental authorities

#### Data Handled

```python
waste_log = {
    "log_id": "WASTE-2025-03-15-001",
    "hospital_id": "H001",
    "generation_date": "2025-03-15",
    "waste_category": "infectious",  # infectious, hazardous, radioactive, general
    
    "waste_details": {
        "type": "Sharps (needles, syringes)",
        "quantity_kg": 12.5,
        "container_type": "Yellow sharps container",
        "container_count": 5,
        "generation_department": "Emergency Department"
    },
    
    "disposal": {
        "pickup_date": "2025-03-16",
        "disposal_company": "SafeWaste Inc.",
        "disposal_facility": "Incinerator-001",
        "manifest_number": "MANIFEST-2025-5678",
        "disposal_method": "Incineration",
        "disposal_certificate": "CERT-2025-1234"
    },
    
    "compliance": {
        "regulatory_authority": "Environmental Protection Agency",
        "compliance_status": "compliant",
        "inspector_notes": ""
    }
}
```

#### Waste Tracking

```python
def track_waste_disposal(waste_log):
    """End-to-end waste tracking"""
    
    # 1. Categorize waste
    category = categorize_waste(waste_log.waste_type)
    
    # 2. Verify proper containerization
    if not verify_container(waste_log.waste_type, waste_log.container_type):
        alert_waste_management_team("Improper containerization")
    
    # 3. Schedule pickup
    pickup = schedule_pickup(
        waste_category=category,
        quantity=waste_log.quantity_kg,
        urgency=calculate_urgency(category)
    )
    
    # 4. Generate manifest
    manifest = generate_waste_manifest(waste_log, pickup)
    
    # 5. Track disposal
    disposal_tracking = {
        "manifest_number": manifest.number,
        "status": "pending_pickup",
        "pickup_scheduled": pickup.datetime,
        "disposal_facility": pickup.facility
    }
    
    # 6. Verify disposal completion
    # (Updated when disposal facility confirms)
    
    # 7. Compliance reporting
    report_to_regulatory_authority(waste_log, manifest)
    
    return disposal_tracking
```

---

## Orchestrator Agents (Backend Reporting)

### 1. Hospital Central Agent

**Agent ID**: `hospital_central_agent_H001`  
**Backend**: Backend Reporting  
**MCP Server**: Orchestrator MCP

#### Purpose

Aggregate and coordinate all department-level reporting within a single hospital.

#### Responsibilities

1. **Department Report Aggregation**
   - Collect reports from all 8 department agents
   - Validate data quality and completeness
   - Resolve inter-department discrepancies

2. **Hospital-Level Analytics**
   - Generate hospital performance dashboards
   - Identify resource bottlenecks
   - Benchmark against national standards

3. **Quality Assurance**
   - Ensure data completeness (no missing required fields)
   - Validate statistical consistency
   - Flag anomalies for review

4. **Submission to NIH**
   - Compile hospital-wide quarterly report
   - Submit to NIH Agent
   - Track submission status

#### Workflow

```python
async def quarterly_reporting_workflow(quarter, year):
    """Hospital Central Agent quarterly workflow"""
    
    # Phase 1: Request reports from department agents (Days 16-25)
    department_agents = [
        "cardiology_agent",
        "maternal_health_agent",
        "infectious_disease_agent",
        "nutrition_agent",
        "mental_health_agent",
        "ncd_agent",
        "endocrinology_agent",
        "oncology_agent"
    ]
    
    department_reports = []
    for agent in department_agents:
        report = await request_report(agent, quarter, year)
        department_reports.append(report)
    
    # Phase 2: Validate reports (Days 26-30)
    validation_results = []
    for report in department_reports:
        validation = validate_report(report)
        if not validation.is_valid:
            request_resubmission(report.department, validation.errors)
        validation_results.append(validation)
    
    # Phase 3: Aggregate hospital-level statistics (Days 31-33)
    hospital_report = {
        "hospital_id": self.hospital_id,
        "quarter": quarter,
        "year": year,
        "department_reports": department_reports,
        "hospital_summary": aggregate_hospital_statistics(department_reports),
        "quality_metrics": calculate_quality_metrics(department_reports),
        "resource_utilization": calculate_resource_utilization(department_reports)
    }
    
    # Phase 4: Hospital administrator review (Days 34-35)
    await request_admin_approval(hospital_report)
    
    # Phase 5: Submit to NIH Agent (Day 36)
    submission = await submit_to_nih_agent(hospital_report)
    
    # Phase 6: Track submission status
    track_submission_status(submission.id)
    
    return hospital_report
```

---

### 2. NIH Agent

**Agent ID**: `nih_agent_national`  
**Backend**: Backend Reporting  
**MCP Server**: NIH MCP

#### Purpose

Aggregate national-level health data and coordinate policy recommendations.

#### Responsibilities

1. **National Data Aggregation**
   - Collect reports from all Hospital Central Agents nationwide
   - Compile national health statistics
   - Identify regional disparities

2. **WHO Reporting**
   - Generate WHO-compliant reports
   - Submit to WHO DHIS2 platform
   - Respond to international health queries

3. **Policy Coordination**
   - Generate evidence-based policy recommendations
   - Coordinate with Ministry of Health
   - Disseminate national health bulletins

4. **Outbreak Coordination**
   - Monitor disease surveillance data
   - Coordinate multi-hospital outbreak responses
   - Activate emergency response protocols

#### National Aggregation

```python
async def aggregate_national_statistics(quarter, year):
    """NIH Agent national aggregation"""
    
    # 1. Collect all hospital reports
    hospitals = get_all_registered_hospitals()
    hospital_reports = []
    
    for hospital in hospitals:
        report = await request_hospital_report(hospital.id, quarter, year)
        hospital_reports.append(report)
    
    # 2. Aggregate by disease category
    national_statistics = {
        "quarter": quarter,
        "year": year,
        "total_hospitals_reporting": len(hospital_reports),
        
        "cardiology": aggregate_cardiology_data(hospital_reports),
        "maternal_health": aggregate_maternal_health_data(hospital_reports),
        "infectious_diseases": aggregate_infectious_disease_data(hospital_reports),
        "nutrition": aggregate_nutrition_data(hospital_reports),
        "mental_health": aggregate_mental_health_data(hospital_reports),
        "ncd": aggregate_ncd_data(hospital_reports),
        "endocrinology": aggregate_endocrinology_data(hospital_reports),
        "oncology": aggregate_oncology_data(hospital_reports)
    }
    
    # 3. Calculate national indicators
    national_indicators = {
        "maternal_mortality_ratio": calculate_mmr(national_statistics),
        "under_5_mortality_rate": calculate_u5mr(national_statistics),
        "disease_burden": calculate_disease_burden(national_statistics),
        "health_system_performance": calculate_health_system_performance(national_statistics)
    }
    
    # 4. Identify regional disparities
    regional_analysis = analyze_regional_disparities(hospital_reports)
    
    # 5. Generate policy recommendations
    policy_recommendations = generate_policy_recommendations(
        national_statistics,
        national_indicators,
        regional_analysis
    )
    
    return {
        "national_statistics": national_statistics,
        "national_indicators": national_indicators,
        "regional_analysis": regional_analysis,
        "policy_recommendations": policy_recommendations
    }
```

---

### 3. R&D Agent

**Agent ID**: `rnd_agent_national`  
**Backend**: Backend Reporting  
**MCP Server**: R&D MCP

#### Purpose

Coordinate research activities and clinical trials across universities and hospitals.

#### Responsibilities

1. **Clinical Trial Management**
   - Register new clinical trials
   - Match patients to eligible trials
   - Track trial progress and outcomes

2. **University Collaboration**
   - Coordinate with University Focal Persons
   - Facilitate research data access
   - Support grant proposal development

3. **Research Data Provision**
   - Anonymize datasets for research
   - Ensure IRB compliance
   - Track data usage and publications

4. **Innovation Pipeline**
   - Identify research opportunities from health data
   - Coordinate translational research
   - Support evidence-based innovation

#### Clinical Trial Coordination

```python
async def match_patients_to_trials(clinical_trial):
    """Match eligible patients to clinical trials"""
    
    # 1. Get trial eligibility criteria
    inclusion_criteria = clinical_trial.inclusion_criteria
    exclusion_criteria = clinical_trial.exclusion_criteria
    
    # 2. Query anonymized patient database
    eligible_patients = []
    
    for hospital in get_participating_hospitals(clinical_trial):
        # Query with privacy-preserving protocols
        patients = await query_eligible_patients(
            hospital_id=hospital.id,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            anonymized=True
        )
        eligible_patients.extend(patients)
    
    # 3. Notify hospital coordinators
    for patient in eligible_patients:
        notify_hospital_coordinator(
            hospital_id=patient.hospital_id,
            patient_pseudonym=patient.pseudonym,
            trial_info=clinical_trial
        )
    
    # 4. Track enrollment
    enrollment_tracking = {
        "trial_id": clinical_trial.id,
        "eligible_patients": len(eligible_patients),
        "enrolled_patients": 0,
        "target_enrollment": clinical_trial.target_enrollment
    }
    
    return enrollment_tracking
```

---

## Agent Communication Protocols

### Message Format

All inter-agent communication follows this standardized format:

```python
agent_message = {
    "message_id": "MSG-2025-03-15-12345",
    "timestamp": "2025-03-15T14:30:00Z",
    "from_agent": "cardiology_agent_H001",
    "to_agent": "hospital_central_agent_H001",
    "message_type": "report_submission",  # report_submission, alert, query, response
    "priority": "normal",  # low, normal, high, critical
    "content": {
        # Message-specific content
    },
    "requires_acknowledgment": true,
    "expiry_time": "2025-03-15T15:30:00Z"  # Optional
}
```

### Communication Channels

1. **Direct API Calls**: For synchronous, low-latency communication
2. **Message Queue (Kafka)**: For asynchronous, high-volume communication
3. **WebSocket**: For real-time updates (emergency scenarios)
4. **MCP Servers**: For coordinated multi-agent workflows

---

## Agent Lifecycle Management

### Agent Initialization

```python
class Agent:
    def __init__(self, agent_id, config):
        self.agent_id = agent_id
        self.config = config
        self.state = "initializing"
        
        # Load configuration
        self.load_config()
        
        # Connect to database
        self.db_connection = self.connect_to_database()
        
        # Connect to MCP server
        self.mcp_connection = self.connect_to_mcp_server()
        
        # Register with orchestrator
        self.register_with_orchestrator()
        
        self.state = "ready"
    
    def load_config(self):
        """Load agent-specific configuration"""
        pass
    
    def connect_to_database(self):
        """Establish database connection"""
        pass
    
    def connect_to_mcp_server(self):
        """Connect to appropriate MCP server"""
        pass
    
    def register_with_orchestrator(self):
        """Register with Hospital Central or NIH Agent"""
        pass
```

### Health Monitoring

```python
def agent_health_check():
    """Periodic health check for all agents"""
    
    health_status = {
        "agent_id": self.agent_id,
        "timestamp": datetime.utcnow(),
        "status": "healthy",  # healthy, degraded, unhealthy
        "metrics": {
            "cpu_usage": get_cpu_usage(),
            "memory_usage": get_memory_usage(),
            "database_connection": check_database_connection(),
            "mcp_connection": check_mcp_connection(),
            "message_queue_depth": get_message_queue_depth()
        }
    }
    
    # Report to monitoring system
    report_health_status(health_status)
    
    return health_status
```

---

## Error Handling & Recovery

### Retry Logic

```python
@retry(max_attempts=3, backoff=exponential_backoff)
async def send_message_to_agent(message):
    """Send message with automatic retry"""
    try:
        response = await agent_api.send(message)
        return response
    except NetworkError as e:
        logger.warning(f"Network error sending message: {e}")
        raise  # Will trigger retry
    except AgentUnavailableError as e:
        logger.error(f"Agent unavailable: {e}")
        # Escalate to orchestrator
        notify_orchestrator_of_agent_failure(message.to_agent)
        raise
```

### Graceful Degradation

```python
def handle_agent_failure(failed_agent_id):
    """Handle agent failure gracefully"""
    
    # 1. Mark agent as unavailable
    mark_agent_unavailable(failed_agent_id)
    
    # 2. Redirect traffic to backup agent (if available)
    backup_agent = get_backup_agent(failed_agent_id)
    if backup_agent:
        redirect_traffic(failed_agent_id, backup_agent.id)
    
    # 3. Notify administrators
    alert_administrators(f"Agent {failed_agent_id} has failed")
    
    # 4. Attempt automatic recovery
    attempt_agent_restart(failed_agent_id)
    
    # 5. Log incident
    log_incident({
        "type": "agent_failure",
        "agent_id": failed_agent_id,
        "timestamp": datetime.utcnow(),
        "recovery_action": "Redirected to backup agent" if backup_agent else "Manual intervention required"
    })
```

---

## Conclusion

HealthLink360's agent ecosystem provides **intelligent, autonomous management** of healthcare operations and reporting. Each agent is specialized for its domain while following standardized protocols for communication, error handling, and lifecycle management.

For department-specific details, see [Department Roles](department_roles.md).
