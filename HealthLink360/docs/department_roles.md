# Department Roles & Responsibilities

**Version**: 1.0  
**Last Updated**: December 2025  
**Document Type**: Operational Reference

---

## Table of Contents

1. [Overview](#overview)
2. [Department Agent Structure](#department-agent-structure)
3. [Cardiology Department](#cardiology-department)
4. [Maternal Health Department (OBGYN)](#maternal-health-department-obgyn)
5. [Infectious Diseases Department](#infectious-diseases-department)
6. [Nutrition Department](#nutrition-department)
7. [Mental Health Department](#mental-health-department)
8. [Non-Communicable Diseases (NCD) Department](#non-communicable-diseases-ncd-department)
9. [Endocrinology Department](#endocrinology-department)
10. [Oncology Department](#oncology-department)
11. [Inter-Department Coordination](#inter-department-coordination)
12. [Reporting Standards](#reporting-standards)

---

## Overview

HealthLink360's **Department Agents** are specialized AI systems responsible for managing department-specific healthcare data, generating analytical reports, and coordinating with hospital and national-level orchestrators. Each department agent operates within the **Backend Reporting** system and follows standardized protocols for data collection, aggregation, and dissemination.

### Key Responsibilities

All department agents share these core responsibilities:

1. **Data Collection**: Gather department-specific data from operational systems
2. **Quality Assurance**: Validate data completeness and accuracy
3. **Aggregation**: Compile quarterly statistical reports
4. **Analysis**: Identify trends, patterns, and anomalies
5. **Reporting**: Submit reports to Hospital Central Agent
6. **Coordination**: Collaborate with other department agents and orchestrators
7. **Compliance**: Ensure adherence to WHO, NIH, and national standards

---

## Department Agent Structure

Each department agent follows a standardized architecture:

```python
class DepartmentAgent:
    """Base class for all department agents"""
    
    def __init__(self, hospital_id, department_name):
        self.hospital_id = hospital_id
        self.department_name = department_name
        self.reporting_period = None
        
    def collect_data(self, start_date, end_date):
        """Collect raw data from operational systems"""
        
    def validate_data(self, data):
        """Ensure data quality and completeness"""
        
    def aggregate_statistics(self, data):
        """Compile statistical summaries"""
        
    def analyze_trends(self, statistics):
        """Identify patterns and anomalies"""
        
    def generate_report(self, statistics, analysis):
        """Create formatted quarterly report"""
        
    def submit_to_hospital_central(self, report):
        """Submit report to Hospital Central Agent"""
        
    def coordinate_with_peers(self, message):
        """Inter-department communication"""
```

---

## Cardiology Department

### Overview

The **Cardiology Agent** manages all cardiac care data, from preventive screenings to complex interventional procedures. It plays a critical role in tracking cardiovascular disease burden, which is a leading cause of mortality globally.

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Cardiac catheterization lab records
- Echocardiography reports
- Stress test results
- Cardiac surgery logs
- Outpatient cardiology consultations
- Emergency cardiac admissions

**Data Points**:
- Patient demographics (age, gender, risk factors)
- Diagnosis codes (ICD-10: I00-I99)
- Procedures performed (angioplasty, stenting, bypass surgery)
- Medications prescribed (anticoagulants, statins, beta-blockers)
- Outcomes (mortality, readmission, complications)

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
cardiology_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "patient_volume": {
        "total_patients": 1250,
        "new_patients": 320,
        "follow_up_patients": 930,
        "emergency_admissions": 180
    },
    
    "disease_prevalence": {
        "coronary_artery_disease": 450,
        "heart_failure": 280,
        "arrhythmias": 190,
        "valvular_disease": 120,
        "congenital_heart_disease": 45
    },
    
    "procedures": {
        "angiography": 210,
        "angioplasty_stenting": 145,
        "cabg_surgery": 32,
        "pacemaker_implantation": 28,
        "echocardiography": 890
    },
    
    "outcomes": {
        "in_hospital_mortality": 12,
        "30_day_readmission_rate": 8.5,  # percentage
        "procedure_complications": 6,
        "average_length_of_stay": 4.2  # days
    },
    
    "risk_factors": {
        "hypertension": 720,
        "diabetes": 380,
        "smoking": 290,
        "obesity": 410,
        "family_history": 520
    }
}
```

#### 3. **Decision-Making Authority**

The Cardiology Agent can:

- **Recommend** cardiac care protocol updates based on outcome data
- **Request** additional cardiac equipment (cath lab, echo machines)
- **Alert** Hospital Central Agent to rising cardiac emergency admissions
- **Propose** preventive cardiology programs based on risk factor prevalence

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **NCD Agent**: Shared patients with diabetes, hypertension
- **Endocrinology Agent**: Diabetic patients with cardiac complications
- **NIH Agent**: National cardiac disease burden reporting
- **Hospital Central Agent**: Resource allocation requests

**Communication Protocol**:
```python
# Example: Alert NCD Agent about diabetic cardiac patients
message = {
    "from": "cardiology_agent",
    "to": "ncd_agent",
    "type": "data_sharing",
    "content": {
        "diabetic_cardiac_patients": 380,
        "recommendation": "Joint diabetes-cardiology clinic"
    }
}
```

---

## Maternal Health Department (OBGYN)

### Overview

The **Maternal Health Agent** focuses on prenatal, delivery, and postnatal care, with the critical goal of reducing maternal and neonatal mortality. This agent is essential for tracking Sustainable Development Goal (SDG) 3.1 (maternal mortality ratio).

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Antenatal clinic records
- Delivery room logs
- Postnatal care records
- High-risk pregnancy monitoring
- Neonatal intensive care unit (NICU) data

**Data Points**:
- Number of pregnancies registered
- Antenatal care visits (ANC1, ANC4+)
- Delivery outcomes (live births, stillbirths, maternal deaths)
- Delivery methods (vaginal, cesarean section)
- Complications (eclampsia, hemorrhage, sepsis)
- Neonatal outcomes (birth weight, Apgar scores, neonatal deaths)

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
maternal_health_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "antenatal_care": {
        "pregnancies_registered": 580,
        "anc1_coverage": 92.5,  # percentage
        "anc4_plus_coverage": 78.3,  # percentage
        "high_risk_pregnancies": 87
    },
    
    "deliveries": {
        "total_deliveries": 520,
        "live_births": 512,
        "stillbirths": 8,
        "vaginal_deliveries": 312,
        "cesarean_sections": 208,
        "cesarean_rate": 40.0  # percentage
    },
    
    "maternal_outcomes": {
        "maternal_deaths": 2,
        "maternal_mortality_ratio": 385,  # per 100,000 live births
        "complications": {
            "postpartum_hemorrhage": 18,
            "eclampsia": 12,
            "sepsis": 5,
            "obstructed_labor": 9
        }
    },
    
    "neonatal_outcomes": {
        "neonatal_deaths": 15,
        "neonatal_mortality_rate": 29.3,  # per 1,000 live births
        "low_birth_weight": 78,
        "preterm_births": 62,
        "nicu_admissions": 94
    },
    
    "postnatal_care": {
        "postnatal_visits_within_48hrs": 450,
        "postnatal_coverage": 86.5  # percentage
    }
}
```

#### 3. **Decision-Making Authority**

The Maternal Health Agent can:

- **Recommend** maternal care policy changes (e.g., mandatory ANC4+ for high-risk)
- **Request** additional NICU equipment or staff
- **Alert** Hospital Central Agent to rising maternal mortality
- **Propose** community outreach programs for antenatal care

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **Nutrition Agent**: Maternal malnutrition and fetal growth
- **Infectious Diseases Agent**: Maternal infections (HIV, syphilis)
- **NIH Agent**: National maternal mortality reporting
- **Hospital Central Agent**: Emergency obstetric care resources

---

## Infectious Diseases Department

### Overview

The **Infectious Diseases Agent** is responsible for disease surveillance, outbreak detection, and epidemic response. This agent is critical for early warning systems and compliance with International Health Regulations (IHR).

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Laboratory confirmed cases
- Syndromic surveillance data
- Vaccination records
- Outbreak investigation reports
- Contact tracing logs

**Data Points**:
- Disease incidence by ICD-10 code
- Geographic distribution of cases
- Age and demographic breakdown
- Vaccination coverage rates
- Outbreak clusters and attack rates

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
infectious_disease_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "disease_surveillance": [
        {
            "disease": "Tuberculosis",
            "icd10_code": "A15-A19",
            "cases": 45,
            "deaths": 3,
            "case_fatality_rate": 6.7
        },
        {
            "disease": "Malaria",
            "icd10_code": "B50-B54",
            "cases": 120,
            "deaths": 2,
            "case_fatality_rate": 1.7
        },
        {
            "disease": "Dengue",
            "icd10_code": "A90-A91",
            "cases": 78,
            "deaths": 1,
            "case_fatality_rate": 1.3
        },
        {
            "disease": "COVID-19",
            "icd10_code": "U07.1",
            "cases": 230,
            "deaths": 8,
            "case_fatality_rate": 3.5
        }
    ],
    
    "outbreaks": [
        {
            "disease": "Measles",
            "start_date": "2025-02-10",
            "end_date": "2025-03-05",
            "total_cases": 34,
            "attack_rate": 12.5,  # per 1,000 population
            "response_measures": "Mass vaccination campaign"
        }
    ],
    
    "vaccination_coverage": {
        "measles": 87.5,
        "polio": 92.3,
        "dpt": 89.1,
        "bcg": 94.2,
        "covid19": 68.7
    },
    
    "antimicrobial_resistance": {
        "mrsa_prevalence": 18.5,  # percentage of S. aureus isolates
        "esbl_prevalence": 32.1   # percentage of E. coli isolates
    }
}
```

#### 3. **Decision-Making Authority**

The Infectious Diseases Agent can:

- **Issue** outbreak alerts to Hospital Central Agent and NIH Agent
- **Recommend** quarantine or isolation measures
- **Request** emergency vaccine supplies
- **Propose** targeted vaccination campaigns

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **NIH Agent**: Real-time outbreak reporting (within 24 hours)
- **Hospital Central Agent**: Resource mobilization for outbreak response
- **Maternal Health Agent**: Maternal infections (HIV, syphilis, hepatitis)
- **WHO**: International Health Regulations (IHR) notifications

**Critical Alert Protocol**:
```python
# Outbreak detected - immediate escalation
alert = {
    "from": "infectious_disease_agent",
    "to": ["hospital_central_agent", "nih_agent"],
    "priority": "CRITICAL",
    "type": "outbreak_alert",
    "content": {
        "disease": "Measles",
        "cases": 34,
        "geographic_cluster": "District A",
        "recommended_action": "Mass vaccination campaign"
    },
    "timestamp": "2025-02-10T14:30:00Z"
}
```

---

## Nutrition Department

### Overview

The **Nutrition Agent** tracks malnutrition, dietary interventions, and food security metrics. Malnutrition is a major contributor to child mortality and maternal health complications.

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Anthropometric measurements (height, weight, MUAC)
- Dietary assessments
- Therapeutic feeding program records
- Micronutrient supplementation logs

**Data Points**:
- Prevalence of stunting, wasting, underweight
- Micronutrient deficiencies (iron, vitamin A, iodine)
- Therapeutic feeding program outcomes
- Dietary diversity scores

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
nutrition_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "child_malnutrition": {
        "children_screened": 1250,
        "stunting_prevalence": 28.5,  # percentage
        "wasting_prevalence": 12.3,
        "underweight_prevalence": 18.7,
        "severe_acute_malnutrition": 45
    },
    
    "therapeutic_feeding": {
        "admissions": 52,
        "cured": 44,
        "deaths": 2,
        "defaulted": 6,
        "cure_rate": 84.6  # percentage
    },
    
    "micronutrient_supplementation": {
        "vitamin_a_coverage": 78.5,
        "iron_supplementation": 82.3,
        "deworming_coverage": 75.8
    },
    
    "maternal_nutrition": {
        "pregnant_women_screened": 420,
        "anemia_prevalence": 45.2,
        "iron_folic_acid_coverage": 88.5
    },
    
    "dietary_diversity": {
        "households_assessed": 320,
        "adequate_dietary_diversity": 62.5  # percentage
    }
}
```

#### 3. **Decision-Making Authority**

The Nutrition Agent can:

- **Recommend** nutrition program expansions
- **Request** therapeutic food supplies
- **Alert** to rising malnutrition rates
- **Propose** community nutrition education programs

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **Maternal Health Agent**: Maternal anemia and fetal growth
- **Pediatrics Agent**: Child growth monitoring
- **NIH Agent**: National nutrition surveillance
- **Hospital Central Agent**: Therapeutic feeding program resources

---

## Mental Health Department

### Overview

The **Mental Health Agent** manages mental health service data with strict confidentiality protocols. Mental health is increasingly recognized as a critical component of overall health.

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Psychiatric consultations
- Therapy session logs (de-identified)
- Medication management records
- Crisis intervention logs
- Suicide prevention hotline data

**Data Points**:
- Mental health service utilization
- Diagnosis distribution (depression, anxiety, psychosis)
- Treatment modalities (medication, psychotherapy, ECT)
- Outcomes (symptom improvement, functional status)
- Suicide attempts and completions

#### 2. **Aggregation Logic**

**Quarterly Metrics** (All data de-identified):

```python
mental_health_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "service_utilization": {
        "total_consultations": 680,
        "new_patients": 145,
        "follow_up_patients": 535,
        "crisis_interventions": 42
    },
    
    "diagnosis_distribution": {
        "depression": 245,
        "anxiety_disorders": 180,
        "bipolar_disorder": 68,
        "schizophrenia": 52,
        "substance_use_disorder": 95,
        "other": 40
    },
    
    "treatment_modalities": {
        "medication_only": 320,
        "psychotherapy_only": 125,
        "combined_treatment": 235,
        "ect": 8
    },
    
    "outcomes": {
        "symptom_improvement": 72.5,  # percentage
        "functional_improvement": 68.3,
        "treatment_adherence": 78.9
    },
    
    "suicide_data": {
        "suicide_attempts": 18,
        "suicide_completions": 3,
        "hotline_calls": 156
    }
}
```

#### 3. **Decision-Making Authority**

The Mental Health Agent can:

- **Recommend** mental health resource allocation
- **Request** additional psychiatrists or therapists
- **Alert** to rising suicide rates
- **Propose** community mental health programs

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **NIH Agent**: National mental health statistics (anonymized)
- **Hospital Central Agent**: Mental health service capacity
- **Maternal Health Agent**: Postpartum depression screening
- **Criminal Case Agent**: Forensic psychiatric evaluations (separate channel)

**Privacy Protocol**:
```python
# All mental health data is de-identified before sharing
def share_mental_health_data(data):
    anonymized_data = apply_k_anonymity(data, k=5)
    remove_pii(anonymized_data)
    aggregate_to_prevent_reidentification(anonymized_data)
    return anonymized_data
```

---

## Non-Communicable Diseases (NCD) Department

### Overview

The **NCD Agent** manages chronic diseases including diabetes, hypertension, chronic respiratory diseases, and cancer. NCDs are the leading cause of death globally.

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- NCD clinic records
- Chronic disease registries
- Screening program data
- Medication adherence tracking

**Data Points**:
- Disease prevalence (diabetes, hypertension, COPD)
- Risk factor prevalence (smoking, obesity, physical inactivity)
- Treatment adherence rates
- Complication rates (diabetic foot, stroke, heart attack)

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
ncd_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "disease_prevalence": {
        "diabetes": 890,
        "hypertension": 1250,
        "copd": 320,
        "asthma": 280,
        "chronic_kidney_disease": 145
    },
    
    "screening_programs": {
        "diabetes_screening": {
            "screened": 2100,
            "newly_diagnosed": 78
        },
        "hypertension_screening": {
            "screened": 2500,
            "newly_diagnosed": 125
        }
    },
    
    "treatment_adherence": {
        "diabetes_medication_adherence": 68.5,  # percentage
        "hypertension_medication_adherence": 72.3
    },
    
    "complications": {
        "diabetic_foot_ulcers": 32,
        "diabetic_retinopathy": 45,
        "stroke": 28,
        "myocardial_infarction": 18,
        "amputations": 8
    },
    
    "risk_factors": {
        "smoking_prevalence": 28.5,
        "obesity_prevalence": 32.8,
        "physical_inactivity": 58.3
    }
}
```

#### 3. **Decision-Making Authority**

The NCD Agent can:

- **Recommend** NCD prevention programs (smoking cessation, exercise)
- **Request** chronic disease management resources
- **Alert** to rising NCD burden
- **Propose** screening program expansions

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **Cardiology Agent**: Cardiovascular complications of diabetes/hypertension
- **Endocrinology Agent**: Diabetes management
- **Oncology Agent**: Cancer as NCD
- **NIH Agent**: National NCD burden reporting

---

## Endocrinology Department

### Overview

The **Endocrinology Agent** manages hormonal disorders including diabetes, thyroid diseases, and metabolic syndromes.

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Endocrine clinic records
- Laboratory results (HbA1c, thyroid function tests)
- Insulin pump and CGM data
- Hormone replacement therapy records

**Data Points**:
- Diabetes type distribution (Type 1, Type 2, gestational)
- Glycemic control metrics (HbA1c levels)
- Thyroid disorder prevalence
- Metabolic syndrome prevalence

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
endocrinology_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "diabetes_management": {
        "type_1_diabetes": 120,
        "type_2_diabetes": 780,
        "gestational_diabetes": 45,
        "hba1c_control": {
            "excellent": 28.5,  # <7%
            "good": 35.2,       # 7-8%
            "poor": 36.3        # >8%
        },
        "insulin_pump_users": 32,
        "cgm_users": 58
    },
    
    "thyroid_disorders": {
        "hypothyroidism": 280,
        "hyperthyroidism": 85,
        "thyroid_nodules": 120,
        "thyroid_cancer": 12
    },
    
    "other_endocrine_disorders": {
        "pcos": 95,
        "adrenal_disorders": 28,
        "pituitary_disorders": 18
    },
    
    "metabolic_syndrome": {
        "prevalence": 32.5  # percentage of screened population
    }
}
```

#### 3. **Decision-Making Authority**

The Endocrinology Agent can:

- **Recommend** diabetes care protocol updates
- **Request** insulin pumps and CGM devices
- **Alert** to poor glycemic control trends
- **Propose** diabetes education programs

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **NCD Agent**: Diabetes as NCD
- **Cardiology Agent**: Diabetic cardiac complications
- **Maternal Health Agent**: Gestational diabetes
- **NIH Agent**: National diabetes prevalence

---

## Oncology Department

### Overview

The **Oncology Agent** manages cancer registry data, treatment outcomes, and clinical trial coordination.

### Responsibilities

#### 1. **Data Collection**

**Sources**:
- Cancer registry
- Pathology reports
- Treatment records (chemotherapy, radiation, surgery)
- Clinical trial enrollment data

**Data Points**:
- Cancer incidence by type and stage
- Treatment modalities
- Survival rates
- Clinical trial participation

#### 2. **Aggregation Logic**

**Quarterly Metrics**:

```python
oncology_report = {
    "hospital_id": "H001",
    "quarter": "Q1",
    "year": 2025,
    
    "cancer_incidence": [
        {
            "cancer_type": "Breast Cancer",
            "icd10_code": "C50",
            "new_cases": 45,
            "stage_distribution": {
                "stage_1": 8,
                "stage_2": 18,
                "stage_3": 12,
                "stage_4": 7
            }
        },
        {
            "cancer_type": "Lung Cancer",
            "icd10_code": "C34",
            "new_cases": 32,
            "stage_distribution": {
                "stage_1": 4,
                "stage_2": 8,
                "stage_3": 12,
                "stage_4": 8
            }
        },
        {
            "cancer_type": "Colorectal Cancer",
            "icd10_code": "C18-C20",
            "new_cases": 28
        }
    ],
    
    "treatment_modalities": {
        "surgery": 68,
        "chemotherapy": 92,
        "radiation_therapy": 54,
        "immunotherapy": 18,
        "palliative_care": 34
    },
    
    "survival_rates": {
        "1_year_survival": 78.5,
        "5_year_survival": 52.3
    },
    
    "clinical_trials": {
        "active_trials": 5,
        "patients_enrolled": 28
    }
}
```

#### 3. **Decision-Making Authority**

The Oncology Agent can:

- **Recommend** cancer screening programs
- **Request** chemotherapy drugs and radiation equipment
- **Alert** to rising cancer incidence
- **Propose** clinical trial opportunities

#### 4. **Inter-Agent Communication**

**Coordinates With**:
- **NCD Agent**: Cancer as NCD
- **R&D Agent**: Clinical trial coordination
- **NIH Agent**: National cancer registry
- **Hospital Central Agent**: Oncology resource allocation

---

## Inter-Department Coordination

### Coordination Mechanisms

#### 1. **Shared Patient Data**

Departments coordinate care for patients with multiple conditions:

```python
# Example: Diabetic patient with cardiac complications
coordination_message = {
    "patient_id": "P12345",  # Pseudonymized
    "primary_department": "endocrinology",
    "consulting_departments": ["cardiology", "ncd"],
    "shared_data": {
        "diagnosis": "Type 2 Diabetes with CAD",
        "medications": ["Metformin", "Atorvastatin", "Aspirin"],
        "care_plan": "Joint endo-cardio clinic"
    }
}
```

#### 2. **Joint Reporting**

Some metrics require collaboration:

- **NCD Agent + Cardiology Agent**: Cardiovascular disease burden
- **Maternal Health Agent + Nutrition Agent**: Maternal anemia
- **Infectious Diseases Agent + Maternal Health Agent**: Maternal HIV

#### 3. **Resource Sharing**

Departments coordinate on shared resources:

- Laboratory services
- Imaging facilities
- Operating rooms
- Specialist consultations

---

## Reporting Standards

### Data Quality Standards

All department agents must ensure:

1. **Completeness**: No missing required fields
2. **Accuracy**: Data validated against source systems
3. **Timeliness**: Reports submitted within 10 days of quarter end
4. **Consistency**: Standardized coding (ICD-10, SNOMED CT)

### Report Format

All reports follow this structure:

```json
{
  "report_metadata": {
    "hospital_id": "H001",
    "department": "cardiology",
    "quarter": "Q1",
    "year": 2025,
    "submitted_at": "2025-04-10T14:30:00Z",
    "submitted_by": "cardiology_agent",
    "version": "1.0"
  },
  
  "data_quality_metrics": {
    "completeness": 98.5,
    "accuracy": 99.2,
    "timeliness": "on_time"
  },
  
  "department_specific_data": {
    // Department-specific metrics
  },
  
  "analysis_and_recommendations": {
    "key_findings": [],
    "trends": [],
    "recommendations": []
  }
}
```

### Compliance Requirements

- **WHO Standards**: ICD-10 coding, DHIS2 compatibility
- **NIH Standards**: National health data dictionary compliance
- **Privacy**: All PII redacted before submission
- **Audit Trail**: All data changes logged

---

## Conclusion

HealthLink360's department agents provide **specialized, intelligent management** of healthcare data across all major medical specialties. Through standardized protocols and inter-agent coordination, the system ensures comprehensive, high-quality health data for decision-making at hospital, national, and international levels.

For operational details on specific agents, refer to:
- [Agent Roles](agent_roles.md)
- [Workflows](workflows.md)
- [API Endpoints](api_endpoints.md)
