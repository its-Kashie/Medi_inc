# all_agents.py - Complete Multi-Department Agent System
import asyncio
import json
from datetime import datetime
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import os
# ===== LOAD ENV =====
from dotenv import load_dotenv
# ===== ADD THIS NEW LINE =====
from agent_key_manager import apply_key_to_agent   # ← yehi line daal do
load_dotenv()

# ===== GEMINI SETUP =====
GEMINI_API_KEY = 'AIzaSyAGuTmYOL7whYOHdRm2yFhlvhj-XInNIlU'


client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# ===== MONGODB SETUP (Shared) =====
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["healthcare360_full"]

# ===== HOSPITALS LIST (Shared) =====
HOSPITALS = [
    "Mayo Hospital",
    "Services Hospital Lahore",
    "Jinnah Hospital Lahore",
    "Sir Ganga Ram Hospital",
    "Shalamar Hospital",
    "Lady Willingdon Hospital",
    "Fatima Memorial Hospital",
    "Shaukat Khanum Memorial",
    "PKLI Lahore",
    "Bahria International"
]

# ===== MCP SERVERS (Shared) =====
orchestrator_mcp = MCPServerStdio(
    params={"command": "python", "args": ["agent_orchestrator_mcp.py"]},
    cache_tools_list=True,
    name="OrchestratorMCP"
)

agents_mcp = MCPServerStdio(
    params={"command": "python", "args": ["agents_mcp_server.py"]},
    cache_tools_list=True,
    name="agents_mcp"
)

# ===== SHARED UTILITY FUNCTIONS =====
def get_focal_person(hospital: str, department: str) -> dict:
    """Get focal person from Excel for any department"""
    try:
        df = pd.read_excel("focal_persons_excels/hospital_focal_persons.xlsx")
        row = df[
            (df['Hospital'] == hospital) &
            (df['Department'] == department)
            ].iloc[0]

        return {
            "name": row['Focal Person Name'],
            "email": row['Email'],
            "phone": row['Contact']
        }
    except Exception as e:
        return {"name": "Unknown", "email": "unknown@example.com", "phone": "N/A"}

def get_quarter_dates(quarter: str, year: int) -> tuple:
    """Convert quarter string to date range"""
    quarter_dates = {
        "Q1": (f"{year}-01-01", f"{year}-03-31"),
        "Q2": (f"{year}-04-01", f"{year}-06-30"),
        "Q3": (f"{year}-07-01", f"{year}-09-30"),
        "Q4": (f"{year}-10-01", f"{year}-12-31")
    }
    return quarter_dates[quarter]

def create_base_graph(title: str, data: dict, chart_type: str = "bar") -> str:
    """Generate base64 encoded graph"""
    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "bar":
        ax.bar(data.keys(), data.values(), color='#3b82f6')
    elif chart_type == "pie":
        ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')

    ax.set_title(title)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    graph_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return graph_b64

# =============================================
# 1. INFECTIOUS DISEASES AGENT
# =============================================
def generate_infectious_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate water-borne diseases report"""
    collection = db["infectious_diseases"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    disease_counts = {}
    water_sources = {}
    outcomes = {"Recovered": 0, "Referred": 0, "Died": 0}

    for rec in records:
        disease = rec.get("disease_category", "Unknown")
        disease_counts[disease] = disease_counts.get(disease, 0) + 1

        water = rec.get("water_source_reported", "Unknown")
        water_sources[water] = water_sources.get(water, 0) + 1

        outcome = rec.get("outcome", "Unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    mortality_rate = (outcomes["Died"] / total * 100) if total > 0 else 0

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Infectious Diseases",
        "total_patients": total,
        "disease_distribution": disease_counts,
        "water_sources": water_sources,
        "outcomes": outcomes,
        "mortality_rate": round(mortality_rate, 2),
        "focal_person": get_focal_person(hospital, "Infectious Diseases"),
        "generated_at": datetime.now().isoformat()
    }

infectious_diseases_agent = Agent(
    name="InfectiousDiseasesAgent",
    model=gemini_model,
    instructions=(
        "🦠 **INFECTIOUS DISEASES (Water-borne) AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Cholera, Typhoid, E. coli, Rotavirus\n"
        "**Database:** healthcare360_full.infectious_diseases\n\n"
        "**Commands:**\n"
        "- Generate single hospital report: generate_infectious_report(hospital, quarter, year)\n"
        "- Generate all hospitals: Loop through HOSPITALS list\n"
        "- Track: disease categories, water sources, dehydration, outcomes\n\n"
        "**Orchestrator Integration:**\n"
        "- handoff_to_agent('infectious_diseases', 'hospital_central', 'report_submission', report, 'normal')\n"
        "- handoff_to_agent('infectious_diseases', 'nih', 'national_data', all_reports, 'high')\n\n"
        "**Analysis Focus:**\n"
        "1. Outbreak detection (>30% single disease)\n"
        "2. Contaminated water exposure (>50% from wells/rivers)\n"
        "3. Mortality trends (>5% concerning)\n"
        "4. Severe dehydration cases\n\n"
        "Always include focal person details and actionable recommendations."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)
apply_key_to_agent("infectious_diseases", infectious_diseases_agent)

# =============================================
# 2. MATERNAL HEALTH AGENT
# =============================================
def generate_maternal_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate maternal & neonatal health report"""
    collection = db["maternal_health"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "registration_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    delivery_types = {"Normal": 0, "C-section": 0}
    maternal_complications = {}
    neonatal_complications = {}
    outcomes = {}
    high_risk_count = 0

    for rec in records:
        delivery_types[rec.get("delivery_type", "Normal")] += 1

        mat_comp = rec.get("maternal_complication", "None")
        maternal_complications[mat_comp] = maternal_complications.get(mat_comp, 0) + 1

        neo_comp = rec.get("neonatal_complication", "None")
        neonatal_complications[neo_comp] = neonatal_complications.get(neo_comp, 0) + 1

        outcome = rec.get("outcome", "Unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

        # High risk factors
        if rec.get("hypertension") == "Yes" or rec.get("diabetes_status") == "Positive":
            high_risk_count += 1

    c_section_rate = (delivery_types["C-section"] / total * 100) if total > 0 else 0
    maternal_mortality = outcomes.get("Maternal death", 0)

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Maternal Health",
        "total_patients": total,
        "delivery_types": delivery_types,
        "c_section_rate": round(c_section_rate, 2),
        "maternal_complications": maternal_complications,
        "neonatal_complications": neonatal_complications,
        "outcomes": outcomes,
        "maternal_mortality": maternal_mortality,
        "high_risk_cases": high_risk_count,
        "focal_person": get_focal_person(hospital, "Obstetrics & Gynecology"),
        "generated_at": datetime.now().isoformat()
    }

maternal_health_agent = Agent(
    name="MaternalHealthAgent",
    model=gemini_model,
    instructions=(
        "🤰 **MATERNAL HEALTH (Obstetrics & Gynecology) AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Maternal health, neonatal outcomes, delivery complications\n"
        "**Database:** healthcare360_full.maternal_health\n\n"
        "**Key Metrics:**\n"
        "- C-section rate (target <30%)\n"
        "- Maternal mortality (target <0.5%)\n"
        "- High-risk pregnancies (hypertension, diabetes)\n"
        "- Neonatal complications\n"
        "- Antenatal visit compliance\n\n"
        "**Red Flags:**\n"
        "- C-section rate >40%\n"
        "- Maternal deaths >2 per quarter\n"
        "- Preeclampsia/hemorrhage trends\n"
        "- Low antenatal visit coverage\n\n"
        "**Orchestrator Integration:**\n"
        "- Submit to hospital_central for facility review\n"
        "- Send to NIH for national maternal health monitoring\n"
        "- Coordinate with nutrition_agent for BMI concerns\n\n"
        "Always provide evidence-based recommendations aligned with WHO guidelines."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)

apply_key_to_agent("maternal_health", maternal_health_agent)

# =============================================
# 3. NUTRITION AGENT
# =============================================
def generate_nutrition_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate nutrition & dietetics report"""
    collection = db["nutrition_data"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    stunting_cases = sum(1 for r in records if r.get("stunted") == "Yes")
    supplements = {}
    age_groups = {"0-12m": 0, "13-24m": 0, "25-59m": 0, "60m+": 0}

    for rec in records:
        supp = rec.get("supplement_given", "None")
        supplements[supp] = supplements.get(supp, 0) + 1

        age = rec.get("age_months", 0)
        if age <= 12:
            age_groups["0-12m"] += 1
        elif age <= 24:
            age_groups["13-24m"] += 1
        elif age <= 59:
            age_groups["25-59m"] += 1
        else:
            age_groups["60m+"] += 1

    stunting_rate = (stunting_cases / total * 100) if total > 0 else 0

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Nutrition",
        "total_patients": total,
        "stunting_cases": stunting_cases,
        "stunting_rate": round(stunting_rate, 2),
        "supplements_distributed": supplements,
        "age_distribution": age_groups,
        "focal_person": get_focal_person(hospital, "Nutrition & Dietetics"),
        "generated_at": datetime.now().isoformat()
    }

nutrition_agent = Agent(
    name="NutritionAgent",
    model=gemini_model,
    instructions=(
        "🥗 **NUTRITION & DIETETICS AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Child malnutrition, stunting, micronutrient deficiencies\n"
        "**Database:** healthcare360_full.nutrition_data\n\n"
        "**Key Indicators:**\n"
        "- Stunting rate (target <20%)\n"
        "- Weight-for-height Z-scores\n"
        "- Supplement distribution (Iron, Vitamin A)\n"
        "- Maternal BMI trends\n\n"
        "**Analysis Points:**\n"
        "1. Stunting hotspots (>30% concerning)\n"
        "2. Age-specific vulnerabilities (0-24 months critical)\n"
        "3. Supplement coverage gaps\n"
        "4. Seasonal variations in malnutrition\n\n"
        "**Interventions:**\n"
        "- Ready-to-use therapeutic food (RUTF) programs\n"
        "- Community nutrition education\n"
        "- Growth monitoring protocols\n\n"
        "Coordinate with maternal_health_agent for pregnancy nutrition."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)
apply_key_to_agent("nutrition", nutrition_agent)

# =============================================
# 4. MENTAL HEALTH AGENT
# =============================================
def generate_mental_health_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate psychiatry/mental health report"""
    collection = db["mental_health_data"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    diagnoses = {}
    suicide_risk = {"Low": 0, "Moderate": 0, "High": 0}
    outcomes = {}
    high_risk_cases = 0

    for rec in records:
        diag = rec.get("diagnosis", "None")
        diagnoses[diag] = diagnoses.get(diag, 0) + 1

        risk = rec.get("suicide_risk", "Low")
        suicide_risk[risk] = suicide_risk.get(risk, 0) + 1

        outcome = rec.get("outcome", "Unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

        if risk in ["Moderate", "High"]:
            high_risk_cases += 1

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Mental Health",
        "total_patients": total,
        "diagnoses": diagnoses,
        "suicide_risk_levels": suicide_risk,
        "high_risk_cases": high_risk_cases,
        "outcomes": outcomes,
        "focal_person": get_focal_person(hospital, "Psychiatry"),
        "generated_at": datetime.now().isoformat()
    }

mental_health_agent = Agent(
    name="MentalHealthAgent",
    model=gemini_model,
    instructions=(
        "🧠 **MENTAL HEALTH (Psychiatry) AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Depression, anxiety, psychosis, substance use\n"
        "**Database:** healthcare360_full.mental_health_data\n\n"
        "**Critical Monitoring:**\n"
        "- Suicide risk assessment (PHQ-9, GAD-7 scores)\n"
        "- High-risk cases (immediate intervention)\n"
        "- Treatment adherence\n"
        "- Counseling session attendance\n\n"
        "**Red Flags:**\n"
        "- Suicide risk >5% of cases\n"
        "- Deteriorating outcomes >10%\n"
        "- Long wait times for first appointments\n"
        "- High dropout rates\n\n"
        "**Privacy & Ethics:**\n"
        "- All mental health data highly confidential\n"
        "- Aggregate reporting only (no patient identifiers)\n"
        "- Stigma-sensitive language\n\n"
        "**Interventions:**\n"
        "- Crisis hotline referrals\n"
        "- Community mental health programs\n"
        "- Anti-stigma campaigns\n\n"
        "Always prioritize patient safety and confidentiality."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)

apply_key_to_agent("mental_health", mental_health_agent)

# =============================================
# 5. NCD INTERNAL MEDICINE AGENT
# =============================================
def generate_ncd_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate non-communicable diseases report"""
    collection = db["ncd_internal_medicine"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    diagnoses = {}
    outcomes = {}
    admissions = 0

    for rec in records:
        diag = rec.get("primary_ncd_diagnosis", "Unknown")
        diagnoses[diag] = diagnoses.get(diag, 0) + 1

        outcome = rec.get("outcome", "Unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

        if rec.get("admission") == "Yes":
            admissions += 1

    admission_rate = (admissions / total * 100) if total > 0 else 0
    mortality = outcomes.get("Died", 0)

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "NCD Internal Medicine",
        "total_patients": total,
        "diagnoses": diagnoses,
        "outcomes": outcomes,
        "admissions": admissions,
        "admission_rate": round(admission_rate, 2),
        "mortality": mortality,
        "focal_person": get_focal_person(hospital, "Internal Medicine"),
        "generated_at": datetime.now().isoformat()
    }

ncd_agent = Agent(
    name="NCDAgent",
    model=gemini_model,
    instructions=(
        "🏥 **NCD INTERNAL MEDICINE AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** CKD, COPD, Stroke, Liver disease, Hypertension, Asthma\n"
        "**Database:** healthcare360_full.ncd_internal_medicine\n\n"
        "**Key Metrics:**\n"
        "- NCD prevalence by type\n"
        "- Hospital admission rates\n"
        "- Complication management\n"
        "- Mortality trends\n\n"
        "**Prevention Focus:**\n"
        "- Early detection screening programs\n"
        "- Lifestyle modification counseling\n"
        "- Medication adherence tracking\n"
        "- Risk factor management (BP, labs)\n\n"
        "**Coordination:**\n"
        "- Link with cardiology_agent for CVD cases\n"
        "- Link with endocrinology_agent for diabetes\n"
        "- Refer complex cases to tertiary centers\n\n"
        "Emphasize preventive care and chronic disease management protocols."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)
apply_key_to_agent("ncd", ncd_agent)

# =============================================
# 6. CARDIOLOGY AGENT
# =============================================
def generate_cardiology_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate cardiology report"""
    collection = db["cardiology_data"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    ecg_findings = {}
    procedures = {}
    icu_admissions = 0
    mortality = 0

    for rec in records:
        ecg = rec.get("ecg_findings", "Unknown")
        ecg_findings[ecg] = ecg_findings.get(ecg, 0) + 1

        proc = rec.get("procedure", "None")
        procedures[proc] = procedures.get(proc, 0) + 1

        if rec.get("icu_admission") == "Yes":
            icu_admissions += 1

        if rec.get("mortality") == "Died":
            mortality += 1

    mortality_rate = (mortality / total * 100) if total > 0 else 0

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Cardiology",
        "total_patients": total,
        "ecg_findings": ecg_findings,
        "procedures_performed": procedures,
        "icu_admissions": icu_admissions,
        "mortality": mortality,
        "mortality_rate": round(mortality_rate, 2),
        "focal_person": get_focal_person(hospital, "Cardiology"),
        "generated_at": datetime.now().isoformat()
    }

cardiology_agent = Agent(
    name="CardiologyAgent",
    model=gemini_model,
    instructions=(
        "❤️ **CARDIOLOGY AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Ischemic heart disease, arrhythmias, heart failure, procedures\n"
        "**Database:** healthcare360_full.cardiology_data\n\n"
        "**Key Metrics:**\n"
        "- ECG findings distribution\n"
        "- Interventional procedures (angioplasty, bypass)\n"
        "- ICU admission rates\n"
        "- Cardiac mortality\n"
        "- Lipid profile management\n\n"
        "**Quality Indicators:**\n"
        "- Door-to-balloon time (target <90 min)\n"
        "- Post-procedure complications\n"
        "- Secondary prevention adherence\n"
        "- Cardiac rehab program enrollment\n\n"
        "**Resource Planning:**\n"
        "- Cath lab utilization\n"
        "- ICU capacity for cardiac cases\n"
        "- Specialized nursing requirements\n\n"
        "Prioritize acute cardiac events and timely interventions."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)

apply_key_to_agent("cardiology", cardiology_agent)

# =============================================
# 7. ENDOCRINOLOGY (DIABETES) AGENT
# =============================================
def generate_endocrine_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate endocrinology/diabetes report"""
    collection = db["endocrinology_diabetes_data"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    diabetes_types = {}
    complications = {}
    poor_control = 0  # HbA1c > 9

    for rec in records:
        dtype = rec.get("diabetes_type", "Unknown")
        diabetes_types[dtype] = diabetes_types.get(dtype, 0) + 1

        comp = rec.get("complication", "None")
        complications[comp] = complications.get(comp, 0) + 1

        hba1c = rec.get("hba1c", 0)
        if hba1c > 9:
            poor_control += 1

    poor_control_rate = (poor_control / total * 100) if total > 0 else 0

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Endocrinology (Diabetes)",
        "total_patients": total,
        "diabetes_types": diabetes_types,
        "complications": complications,
        "poor_control_cases": poor_control,
        "poor_control_rate": round(poor_control_rate, 2),
        "focal_person": get_focal_person(hospital, "Endocrinology"),
        "generated_at": datetime.now().isoformat()
    }

endocrinology_agent = Agent(
    name="EndocrinologyAgent",
    model=gemini_model,
    instructions=(
        "🩺 **ENDOCRINOLOGY (DIABETES) AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Type 1/2 diabetes, glycemic control, complications\n"
        "**Database:** healthcare360_full.endocrinology_diabetes_data\n\n"
        "**Key Metrics:**\n"
        "- HbA1c control (target <7%)\n"
        "- Complication rates (DKA, nephropathy, retinopathy)\n"
        "- Insulin vs oral therapy distribution\n"
        "- Hypoglycemia events\n\n"
        "**Red Flags:**\n"
        "- >30% patients with HbA1c >9%\n"
        "- Rising DKA admissions\n"
        "- Diabetic foot ulcers\n"
        "- Retinopathy screening gaps\n\n"
        "**Patient Education:**\n"
        "- Self-monitoring blood glucose\n"
        "- Dietary counseling\n"
        "- Exercise programs\n"
        "- Medication adherence\n\n"
        "Coordinate with nutrition_agent and ncd_agent for holistic care."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)
apply_key_to_agent("endocrinology", endocrinology_agent)


# =============================================
# 8. ONCOLOGY AGENT
# =============================================
def generate_oncology_report(hospital: str, quarter: str, year: int) -> dict:
    """Generate oncology report"""
    collection = db["oncology_data"]
    start_date, end_date = get_quarter_dates(quarter, year)

    query = {
        "hospital": hospital,
        "visit_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(collection.find(query))
    total = len(records)

    if total == 0:
        return {"hospital": hospital, "quarter": quarter, "year": year, "total_patients": 0, "error": "No data"}

    # Analytics
    cancer_sites = {}
    stages = {}
    treatments = {}
    late_diagnosis = 0
    mortality = 0

    for rec in records:
        site = rec.get("cancer_site", "Unknown")
        cancer_sites[site] = cancer_sites.get(site, 0) + 1

        stage = rec.get("stage", "Unknown")
        stages[stage] = stages.get(stage, 0) + 1

        treatment = rec.get("treatment_plan", "Unknown")
        treatments[treatment] = treatments.get(treatment, 0) + 1

        if rec.get("late_diagnosis") == "Yes":
            late_diagnosis += 1

        if rec.get("outcome") == "Died":
            mortality += 1

    late_diagnosis_rate = (late_diagnosis / total * 100) if total > 0 else 0
    mortality_rate = (mortality / total * 100) if total > 0 else 0

    return {
        "hospital": hospital,
        "quarter": quarter,
        "year": year,
        "department": "Oncology",
        "total_patients": total,
        "cancer_sites": cancer_sites,
        "stages": stages,
        "treatments": treatments,
        "late_diagnosis_cases": late_diagnosis,
        "late_diagnosis_rate": round(late_diagnosis_rate, 2),
        "mortality": mortality,
        "mortality_rate": round(mortality_rate, 2),
        "focal_person": get_focal_person(hospital, "Oncology"),
        "generated_at": datetime.now().isoformat()
    }

oncology_agent = Agent(
    name="OncologyAgent",
    model=gemini_model,
    instructions=(
        "🎗️ **ONCOLOGY AGENT**\n\n"
        f"**Hospitals:** {', '.join(HOSPITALS)}\n\n"
        "**Focus:** Cancer detection, staging, treatment, outcomes\n"
        "**Database:** healthcare360_full.oncology_data\n\n"
        "**Priority Sites:**\n"
        "- Breast cancer (most common in women)\n"
        "- Oral cancer (high in Pakistan)\n"
        "- Lung cancer\n"
        "- Colorectal cancer\n"
        "- Leukemia\n\n"
        "**Critical Metrics:**\n"
        "- Late-stage diagnosis rate (target <40%)\n"
        "- Stage distribution (I-IV)\n"
        "- Treatment modalities (chemo, surgery, radiation)\n"
        "- Biopsy turnaround times\n"
        "- Mortality rates\n\n"
        "**Early Detection Focus:**\n"
        "- Screening program effectiveness\n"
        "- Public awareness campaigns\n"
        "- Reducing diagnostic delays\n"
        "- Tertiary care referral pathways\n\n"
        "**Quality Indicators:**\n"
        "- Treatment protocol adherence\n"
        "- Multidisciplinary team reviews\n"
        "- Palliative care integration\n"
        "- Survivorship programs\n\n"
        "Emphasize early detection and comprehensive cancer care pathways."
    ),
    mcp_servers=[orchestrator_mcp, agents_mcp]
)

apply_key_to_agent("oncology", oncology_agent)

# =============================================
# AGENT REGISTRY
# =============================================
ALL_AGENTS = {
    "infectious_diseases": {
        "agent": infectious_diseases_agent,
        "generator": generate_infectious_report,
        "description": "Water-borne diseases monitoring"
    },
    "maternal_health": {
        "agent": maternal_health_agent,
        "generator": generate_maternal_report,
        "description": "Maternal & neonatal health tracking"
    },
    "nutrition": {
        "agent": nutrition_agent,
        "generator": generate_nutrition_report,
        "description": "Child nutrition & malnutrition surveillance"
    },
    "mental_health": {
        "agent": mental_health_agent,
        "generator": generate_mental_health_report,
        "description": "Mental health & psychiatry services"
    },
    "ncd": {
        "agent": ncd_agent,
        "generator": generate_ncd_report,
        "description": "Non-communicable diseases management"
    },
    "cardiology": {
        "agent": cardiology_agent,
        "generator": generate_cardiology_report,
        "description": "Cardiac care & interventions"
    },
    "endocrinology": {
        "agent": endocrinology_agent,
        "generator": generate_endocrine_report,
        "description": "Diabetes & endocrine disorders"
    },
    "oncology": {
        "agent": oncology_agent,
        "generator": generate_oncology_report,
        "description": "Cancer detection & treatment"
    }
}

# =============================================
# MASTER REPORT GENERATOR
# =============================================
def generate_department_report(department: str, hospital: str, quarter: str, year: int) -> dict:
    """Universal report generator for any department"""
    if department not in ALL_AGENTS:
        return {"error": f"Unknown department: {department}"}

    generator = ALL_AGENTS[department]["generator"]
    return generator(hospital, quarter, year)

def generate_all_hospitals_report(department: str, quarter: str, year: int) -> dict:
    """Generate reports for all hospitals in a department"""
    if department not in ALL_AGENTS:
        return {"error": f"Unknown department: {department}"}

    generator = ALL_AGENTS[department]["generator"]
    all_reports = []

    for hospital in HOSPITALS:
        report = generator(hospital, quarter, year)
        all_reports.append(report)

    # Aggregate statistics
    total_patients = sum(r.get("total_patients", 0) for r in all_reports)
    total_mortality = sum(r.get("mortality", 0) for r in all_reports)

    return {
        "department": department,
        "quarter": quarter,
        "year": year,
        "total_hospitals": len(HOSPITALS),
        "total_patients": total_patients,
        "total_mortality": total_mortality,
        "national_mortality_rate": round(total_mortality / total_patients * 100, 2) if total_patients > 0 else 0,
        "hospital_reports": all_reports,
        "generated_at": datetime.now().isoformat()
    }

def generate_national_dashboard(quarter: str, year: int) -> dict:
    """Generate complete national dashboard across all departments"""
    dashboard = {
        "quarter": quarter,
        "year": year,
        "generated_at": datetime.now().isoformat(),
        "departments": {}
    }

    for dept_key, dept_info in ALL_AGENTS.items():
        print(f"Generating national data for {dept_key}...")
        dept_report = generate_all_hospitals_report(dept_key, quarter, year)
        dashboard["departments"][dept_key] = dept_report

    # Overall statistics
    total_patients_all = sum(
        dept["total_patients"]
        for dept in dashboard["departments"].values()
    )

    dashboard["overall_statistics"] = {
        "total_patients_all_departments": total_patients_all,
        "total_hospitals": len(HOSPITALS),
        "departments_active": len(ALL_AGENTS)
    }

    return dashboard

# =============================================
# DEMO & TESTING
# =============================================
async def run_comprehensive_demo():
    """Comprehensive demo of all hospital_agents"""

    async with orchestrator_mcp, agents_mcp:
        await orchestrator_mcp.connect()
        await agents_mcp.connect()

        print("=" * 80)
        print("HEALTHCARE360 - ALL DEPARTMENT AGENTS DEMO")
        print("=" * 80)

        # Test 1: Single hospital, single department
        print("\n📊 TEST 1: Single Hospital Report (Services Hospital - Q1 2025)")
        print("-" * 80)

        test_dept = "infectious_diseases"
        test_hospital = "Services Hospital Lahore"
        report = generate_department_report(test_dept, test_hospital, "Q1", 2025)

        print(f"✅ Department: {report['department']}")
        print(f"✅ Hospital: {report['hospital']}")
        print(f"✅ Total Patients: {report['total_patients']}")
        print(f"✅ Focal Person: {report['focal_person']['name']} ({report['focal_person']['email']})")

        # Test 2: All hospitals for one department
        print("\n\n📊 TEST 2: All Hospitals Report (Maternal Health - Q1 2025)")
        print("-" * 80)

        all_hospitals = generate_all_hospitals_report("maternal_health", "Q1", 2025)
        print(f"✅ Total Hospitals: {all_hospitals['total_hospitals']}")
        print(f"✅ Total Patients (All): {all_hospitals['total_patients']}")
        print(f"✅ National Mortality Rate: {all_hospitals['national_mortality_rate']}%")

        # Test 3: Department summary
        print("\n\n📊 TEST 3: All Departments Summary")
        print("-" * 80)

        for dept_key, dept_info in ALL_AGENTS.items():
            sample_report = dept_info["generator"]("Mayo Hospital", "Q1", 2025)
            print(f"✅ {dept_key.upper()}: {sample_report.get('total_patients', 0)} patients")

        # Test 4: National dashboard (small sample)
        print("\n\n📊 TEST 4: National Dashboard Preview (Q1 2025)")
        print("-" * 80)

        # Generate for just 2 departments to save time in demo
        sample_depts = ["infectious_diseases", "cardiology"]
        for dept in sample_depts:
            national = generate_all_hospitals_report(dept, "Q1", 2025)
            print(f"\n{dept.upper()}:")
            print(f"  - Total Patients: {national['total_patients']}")
            print(f"  - Mortality Rate: {national['national_mortality_rate']}%")

        print("\n" + "=" * 80)
        print("✅ ALL AGENTS INITIALIZED AND TESTED SUCCESSFULLY")
        print("=" * 80)

        await orchestrator_mcp.cleanup()
        await agents_mcp.cleanup()

async def run_single_agent_test(agent_name: str):
    """Test a specific agent"""
    if agent_name not in ALL_AGENTS:
        print(f"❌ Unknown agent: {agent_name}")
        print(f"Available hospital_agents: {', '.join(ALL_AGENTS.keys())}")
        return

    async with orchestrator_mcp, agents_mcp:
        await orchestrator_mcp.connect()
        await agents_mcp.connect()

        print(f"\n🔬 Testing {agent_name.upper()} Agent")
        print("=" * 80)

        # Test with Mayo Hospital Q1 2025
        report = generate_department_report(agent_name, "Mayo Hospital", "Q1", 2025)

        print(f"\n📋 Report Summary:")
        print(f"  Hospital: {report.get('hospital', 'N/A')}")
        print(f"  Department: {report.get('department', 'N/A')}")
        print(f"  Quarter: {report.get('quarter', 'N/A')} {report.get('year', 'N/A')}")
        print(f"  Total Patients: {report.get('total_patients', 0)}")

        if 'focal_person' in report:
            fp = report['focal_person']
            print(f"\n👤 Focal Person:")
            print(f"  Name: {fp['name']}")
            print(f"  Email: {fp['email']}")
            print(f"  Phone: {fp['phone']}")

        # Show department-specific metrics
        print(f"\n📊 Key Metrics:")
        for key, value in report.items():
            if key not in ['hospital', 'quarter', 'year', 'department', 'focal_person', 'generated_at',
                           'total_patients']:
                if isinstance(value, dict) and len(value) <= 5:
                    print(f"  {key}: {value}")
                elif not isinstance(value, dict):
                    print(f"  {key}: {value}")

        print("\n✅ Agent test completed successfully")

        await orchestrator_mcp.cleanup()
        await agents_mcp.cleanup()

# =============================================
# CLI INTERFACE
# =============================================
async def main():
    """Main CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\n🏥 Healthcare360 Multi-Agent System")
        print("=" * 80)
        print("\nUsage:")
        print("  python healthcare360_all_agents.py demo          - Run comprehensive demo")
        print("  python healthcare360_all_agents.py test <agent>  - Test specific agent")
        print("  python healthcare360_all_agents.py list          - List all hospital_agents")
        print("  python healthcare360_all_agents.py dashboard <Q> <YEAR> - Generate national dashboard")
        print("\nAvailable hospital_agents:")
        for dept_key, dept_info in ALL_AGENTS.items():
            print(f"  - {dept_key}: {dept_info['description']}")
        print("\nExample:")
        print("  python healthcare360_all_agents.py test infectious_diseases")
        print("  python healthcare360_all_agents.py dashboard Q1 2025")
        return

    command = sys.argv[1].lower()

    if command == "demo":
        await run_comprehensive_demo()

    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ Error: Specify agent name")
            print(f"Available: {', '.join(ALL_AGENTS.keys())}")
            return
        agent_name = sys.argv[2]
        await run_single_agent_test(agent_name)

    elif command == "list":
        print("\n🏥 Healthcare360 Department Agents")
        print("=" * 80)
        for dept_key, dept_info in ALL_AGENTS.items():
            print(f"\n📂 {dept_key.upper()}")
            print(f"   Description: {dept_info['description']}")
            print(f"   Database: healthcare360_full.{dept_key}")
        print("\n" + "=" * 80)

    elif command == "dashboard":
        if len(sys.argv) < 4:
            print("❌ Error: Specify quarter and year")
            print("Example: python healthcare360_all_agents.py dashboard Q1 2025")
            return

        quarter = sys.argv[2].upper()
        year = int(sys.argv[3])

        print(f"\n🌐 Generating National Dashboard - {quarter} {year}")
        print("=" * 80)

        dashboard = generate_national_dashboard(quarter, year)

        # Save to JSON
        output_file = f"national_dashboard_{quarter}_{year}.json"
        with open(output_file, 'w') as f:
            json.dump(dashboard, f, indent=2, default=str)

        print(f"\n✅ Dashboard generated successfully!")
        print(f"📄 Saved to: {output_file}")
        print(f"\n📊 Summary:")
        print(
            f"  Total Patients (All Departments): {dashboard['overall_statistics']['total_patients_all_departments']}")
        print(f"  Active Departments: {dashboard['overall_statistics']['departments_active']}")
        print(f"  Hospitals Covered: {dashboard['overall_statistics']['total_hospitals']}")

    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see usage")

if __name__ == "__main__":
    asyncio.run(main())