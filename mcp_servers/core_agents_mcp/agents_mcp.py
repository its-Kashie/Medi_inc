# agents_mcp.py - FIXED VERSION (Silent - No STDOUT pollution)
import json, time, os, random, sys
from functools import wraps
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from utils import haversine
from local_trace import append_trace
os.environ['MCP_CLIENT_TIMEOUT'] = '10'

# ===== REDIRECT DEBUG OUTPUT TO STDERR =====
def debug_log(msg):
    """Log to STDERR only (STDOUT is reserved for MCP protocol)"""
    print(msg, file=sys.stderr, flush=True)


# ===== MCP Server setup FIRST =====
mcp = FastMCP("Tracking Agent - Lahore Dispatch")
debug_log("✅ agents_mcp: MCP server initialized")


# ===== LAZY IMPORTS =====
def get_mongo():
    """Lazy MongoDB - only connect when needed"""
    global MongoClient, mongo_client, db
    if 'mongo_client' not in globals():
        debug_log("🔄 Connecting to MongoDB...")
        try:
            from pymongo import MongoClient
            mongo_client = MongoClient(
                "mongodb://localhost:27017/",
                serverSelectionTimeoutMS=2000
            )
            db = mongo_client["healthcare360_full"]
            mongo_client.admin.command('ping')
            debug_log("✅ MongoDB connected")
        except Exception as e:
            debug_log(f"⚠️ MongoDB unavailable: {e}")
            mongo_client = None
            db = None
    return mongo_client, db


def get_email():
    """Lazy email imports"""
    global EmailMessage, smtplib, threading
    if 'EmailMessage' not in globals():
        from email.message import EmailMessage
        import smtplib
        import threading
    return EmailMessage, smtplib, threading


def get_plotting():
    """Lazy plotting imports"""
    global pd, plt, matplotlib, io, base64
    if 'pd' not in globals():
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import io
        import base64
    return pd, plt, matplotlib, io, base64


# ===== LOAD MOCK DATA =====
DATA_FILE = os.path.join(os.path.dirname(__file__), "hospitals_lhr.json")
try:
    with open(DATA_FILE, "r") as f:
        DATA = json.load(f)
    HOSPITALS = DATA["hospitals"]
    RESCUE_ORGS = DATA["rescue_orgs"]
    debug_log("✅ Hospital data loaded")
except Exception as e:
    debug_log(f"⚠️ Mock data unavailable: {e}")
    HOSPITALS = []
    RESCUE_ORGS = []

# ===== TRACE LOG =====
TRACE_LOG = []
LAST_DISPATCH_LOG = []


def log_trace(action: str, details: dict):
    """Log actions for debugging"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    TRACE_LOG.append(entry)
    debug_log(f"[TRACE] {action}: {str(details)[:100]}")


def traced_tool(func):
    """Automatic tracing for MCP tools"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        call_id = f"{func.__name__}-{int(time.time() * 1000)}"
        log_trace("tool_call_start", {
            "tool": func.__name__,
            "call_id": call_id
        })
        try:
            result = func(*args, **kwargs)
            log_trace("tool_call_end", {
                "tool": func.__name__,
                "call_id": call_id,
                "status": "success"
            })
            return result
        except Exception as e:
            log_trace("tool_call_error", {
                "tool": func.__name__,
                "call_id": call_id,
                "error": str(e)
            })
            raise

    return wrapper


# ===== COGNITIVE LOGIC =====
def find_nearest_ambulance(lat, lon):
    best = None
    min_dist = 9999
    for group in [HOSPITALS, RESCUE_ORGS]:
        for unit in group:
            for amb in unit["ambulances"]:
                if amb["status"] == "available":
                    dist = haversine(lat, lon, unit["lat"], unit["lon"])
                    if dist < min_dist:
                        min_dist = dist
                        best = {
                            "service": unit["name"],
                            "ambulance_id": amb["id"],
                            "contact": unit["contact"],
                            "distance_km": round(dist, 2),
                            "unit_ref": unit,
                            "amb_ref": amb
                        }
    return best


# ===== TRACKING AGENT TOOLS =====

@mcp.tool()
@traced_tool
def dispatch_nearest_ambulance(lat: float, lon: float) -> dict:
    """Dispatch nearest available ambulance"""
    amb_info = find_nearest_ambulance(lat, lon)
    if not amb_info:
        return {"status": "failed", "message": "No ambulance available nearby"}

    amb_info["amb_ref"]["status"] = "dispatched"
    dispatch_record = {
        "service": amb_info["service"],
        "ambulance_id": amb_info["ambulance_id"],
        "contact": amb_info["contact"],
        "distance_km": amb_info["distance_km"],
        "eta_min": round(amb_info["distance_km"] / 0.5, 1),
        "timestamp": time.time()
    }
    LAST_DISPATCH_LOG.append(dispatch_record)
    return dispatch_record


@mcp.tool()
@traced_tool
def release_ambulance(ambulance_id: str) -> dict:
    """Release ambulance back to available pool"""
    for group in [HOSPITALS, RESCUE_ORGS]:
        for unit in group:
            for amb in unit["ambulances"]:
                if amb["id"] == ambulance_id:
                    amb["status"] = "available"
                    return {
                        "status": "success",
                        "ambulance_id": ambulance_id,
                        "message": "Ambulance is now available"
                    }
    return {"status": "failed", "message": "Ambulance not found"}


@mcp.tool()
@traced_tool
def nearest_hospital_fallback(lat: float, lon: float) -> dict:
    """Degraded mode - find nearest hospital"""
    best = None
    min_dist = 9999
    for hosp in HOSPITALS:
        dist = haversine(lat, lon, hosp["lat"], hosp["lon"])
        if dist < min_dist:
            min_dist = dist
            best = hosp
    return {
        "hospital_name": best["name"],
        "contact": best["contact"],
        "distance_km": round(min_dist, 2)
    }


# ===== MATERNAL HEALTH TOOLS =====

@mcp.tool()
@traced_tool
def maternal_emergency(lat: float, lon: float, emergency_type: str, mother_id: str) -> dict:
    """Emergency handoff to tracking agent"""
    dispatch = dispatch_nearest_ambulance(lat, lon)
    dispatch["emergency_type"] = emergency_type
    dispatch["mother_id"] = mother_id
    return dispatch


@mcp.tool()
@traced_tool
def hms_register_patient(mother_id: str, hospital_id: str = "HMS-LHR-001") -> dict:
    """Register patient with Hospital HMS"""
    return {
        "status": "success",
        "hms_patient_id": f"HMS-{random.randint(10000, 99999)}",
        "hospital_id": hospital_id,
        "hospital_name": "Services Hospital Lahore",
        "assigned_doctor": "Dr. Fatima Malik",
        "department": "Gynecology",
        "registered_at": time.time()
    }


@mcp.tool()
@traced_tool
def nadra_birth_register(mother_cnic: str, baby_name: str, birth_date: str) -> dict:
    """Register birth with NADRA"""
    return {
        "status": "success",
        "birth_certificate_number": f"BC-{random.randint(100000, 999999)}",
        "baby_name": baby_name,
        "mother_cnic": mother_cnic,
        "birth_date": birth_date,
        "nadra_reference": f"NADRA-{random.randint(1000000, 9999999)}"
    }


@mcp.tool()
@traced_tool
def schedule_postpartum_vaccination(mother_id: str) -> dict:
    """Schedule postpartum and newborn vaccinations"""
    vaccination_schedule = [
        {"vaccine": "BCG", "age_days": 0},
        {"vaccine": "OPV-0", "age_days": 0},
        {"vaccine": "Hepatitis B", "age_days": 0},
        {"vaccine": "OPV-1 + Pentavalent-1", "age_days": 42},
        {"vaccine": "OPV-2 + Pentavalent-2", "age_days": 70},
        {"vaccine": "OPV-3 + Pentavalent-3", "age_days": 98},
        {"vaccine": "Measles-1", "age_days": 270},
        {"vaccine": "Measles-2", "age_days": 450}
    ]
    today = time.time()
    for vax in vaccination_schedule:
        vax["scheduled_timestamp"] = today + vax["age_days"] * 86400
    return {"mother_id": mother_id, "vaccinations": vaccination_schedule}


# ===== MATERNAL REGISTRATION & APPOINTMENT TOOLS =====

@mcp.tool()
@traced_tool
def register_maternal_patient(registration_id: str, phone: str, email: str, hospital_id: str = "H001") -> dict:
    """
    Register new maternal patient in hospital database

    Args:
        registration_id: From CNIC service (e.g., REG-1234567890)
        phone: Patient phone number
        email: Patient email
        hospital_id: Hospital identifier

    Returns:
        Patient registration confirmation with patient_id
    """

    # Generate patient ID
    patient_id = f"MAT-{random.randint(10000, 99999)}"

    # Store in MongoDB (in production)
    mongo_client, db = get_mongo()
    if db:
        patients_collection = db["maternal_patients"]

        patient_record = {
            "patient_id": patient_id,
            "registration_id": registration_id,  # Link to CNIC service
            "phone": phone,
            "email": email,
            "hospital_id": hospital_id,
            "registered_at": datetime.now().isoformat(),
            "status": "active",
            "appointments": [],
            "follow_ups": []
        }

        patients_collection.insert_one(patient_record)

    return {
        "status": "registered",
        "patient_id": patient_id,
        "hospital_id": hospital_id,
        "hospital_name": "Services Hospital Lahore",
        "registered_at": datetime.now().isoformat(),
        "confirmation_sent": True
    }


@mcp.tool()
@traced_tool
def generate_appointment_token(patient_id: str, appointment_date: str, appointment_time: str) -> dict:
    """
    Generate appointment token with queue management

    Args:
        patient_id: Maternal patient ID (e.g., MAT-12345)
        appointment_date: Date in YYYY-MM-DD format
        appointment_time: morning/afternoon/evening

    Returns:
        Token with queue position and estimated wait time
    """

    # Check if appointment is today
    today = datetime.now().date()
    appt_date = datetime.fromisoformat(appointment_date).date()
    is_today = today == appt_date

    # Get current queue (mock - in production query database)
    current_queue = random.randint(5, 15) if is_today else 0

    # Generate token number
    token_number = f"TOKEN-{random.randint(10000, 99999)}"

    # Assign doctor based on time slot
    doctors = {
        "morning": "Dr. Fatima Malik",
        "afternoon": "Dr. Ayesha Khan",
        "evening": "Dr. Sara Ahmed"
    }
    doctor_name = doctors.get(appointment_time, "Dr. Fatima Malik")

    # Calculate estimated wait time (15 min per patient)
    wait_time_minutes = current_queue * 15 if is_today else 0
    estimated_time = datetime.now() + timedelta(minutes=wait_time_minutes) if is_today else None

    token_data = {
        "token_number": token_number,
        "patient_id": patient_id,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "doctor_name": doctor_name,
        "queue_position": current_queue + 1 if is_today else "Not yet in queue",
        "estimated_wait_minutes": wait_time_minutes,
        "estimated_time": estimated_time.strftime("%I:%M %p") if estimated_time else "On scheduled date",
        "hospital": "Services Hospital Lahore",
        "department": "Obstetrics & Gynecology",
        "instructions": "Please arrive 15 minutes before your appointment. Bring your CNIC and previous medical records.",
        "generated_at": datetime.now().isoformat()
    }

    # Store token in database
    mongo_client, db = get_mongo()
    if db:
        tokens_collection = db["appointment_tokens"]
        tokens_collection.insert_one(token_data)

    return token_data


@mcp.tool()
@traced_tool
def send_appointment_notification(patient_email: str, token_data: dict) -> dict:
    """
    Send appointment confirmation via email

    Args:
        patient_email: Patient email address
        token_data: Token data from generate_appointment_token

    Returns:
        Notification confirmation
    """

    EmailMessage, smtplib, threading = get_email()

    try:
        subject = f"Appointment Confirmed - {token_data['token_number']}"

        body = f"""
Assalam-o-Alaikum!

Your appointment has been confirmed:

🎫 Token Number: {token_data['token_number']}
📅 Date: {token_data['appointment_date']}
⏰ Time Slot: {token_data['appointment_time'].title()}
👩‍⚕️ Doctor: {token_data['doctor_name']}
📍 Location: {token_data['hospital']} - {token_data['department']}

⏳ Queue Information:
• Position: {token_data['queue_position']}
• Estimated Time: {token_data['estimated_time']}

📋 Instructions:
{token_data['instructions']}

For emergencies, call: 1122

Allah Hafiz,
HealthLink360 Team
        """

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = "nooreasal786@gmail.com"
        msg['To'] = patient_email
        msg.set_content(body)

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
            smtp.starttls()
            smtp.login("nooreasal786@gmail.com", "irph tole tuqr vfmi")
            smtp.send_message(msg)

        return {
            "status": "sent",
            "email": patient_email,
            "notification_type": "appointment_confirmation",
            "sent_at": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
@traced_tool
def schedule_followup_reminders(patient_id: str, delivery_date: str = None) -> dict:
    """
    Schedule automated follow-up reminders

    Args:
        patient_id: Maternal patient ID
        delivery_date: If provided, schedule postpartum reminders

    Returns:
        List of scheduled reminders
    """

    reminders = []
    base_date = datetime.now() if not delivery_date else datetime.fromisoformat(delivery_date)

    if delivery_date:
        # Postpartum reminders
        reminders = [
            {
                "reminder_type": "postpartum_checkup",
                "scheduled_date": (base_date + timedelta(days=3)).isoformat(),
                "message": "Postpartum checkup reminder - Please visit hospital"
            },
            {
                "reminder_type": "vaccination",
                "scheduled_date": (base_date + timedelta(days=42)).isoformat(),
                "message": "Baby vaccination due - First dose"
            },
            {
                "reminder_type": "maternal_checkup",
                "scheduled_date": (base_date + timedelta(days=42)).isoformat(),
                "message": "6-week maternal checkup"
            }
        ]
    else:
        # Prenatal reminders
        reminders = [
            {
                "reminder_type": "anc_checkup",
                "scheduled_date": (base_date + timedelta(days=7)).isoformat(),
                "message": "ANC checkup reminder"
            },
            {
                "reminder_type": "blood_test",
                "scheduled_date": (base_date + timedelta(days=14)).isoformat(),
                "message": "Blood test scheduled"
            },
            {
                "reminder_type": "ultrasound",
                "scheduled_date": (base_date + timedelta(days=21)).isoformat(),
                "message": "Ultrasound appointment"
            }
        ]

    # Store reminders in database
    mongo_client, db = get_mongo()
    if db:
        reminders_collection = db["followup_reminders"]
        for reminder in reminders:
            reminder["patient_id"] = patient_id
            reminder["status"] = "scheduled"
            reminders_collection.insert_one(reminder)

    return {
        "patient_id": patient_id,
        "reminders_scheduled": len(reminders),
        "reminders": reminders
    }


@mcp.tool()
@traced_tool
def detect_mental_health_concerns(patient_message: str, patient_id: str) -> dict:
    """
    Detect mental health keywords and determine if handoff to Mental Agent needed

    Args:
        patient_message: What the patient said
        patient_id: Patient identifier

    Returns:
        Detection result with handoff recommendation
    """

    mental_health_keywords = [
        "depression", "depressed", "udaas", "ghabrati",
        "anxiety", "stress", "tension", "pareshani",
        "suicidal", "khudkushi", "zindagi se tang",
        "crying", "rona", "ro rahi hoon",
        "lonely", "akeli", "koi nahi hai",
        "scared", "dar lag raha"
    ]

    message_lower = patient_message.lower()
    detected_keywords = [kw for kw in mental_health_keywords if kw in message_lower]

    needs_handoff = len(detected_keywords) > 0
    severity = "high" if any(
        word in message_lower for word in ["suicidal", "khudkushi"]) else "moderate" if needs_handoff else "low"

    return {
        "mental_health_detected": needs_handoff,
        "severity": severity,
        "detected_keywords": detected_keywords,
        "recommendation": "handoff_to_mental_agent" if needs_handoff else "continue_normal_care",
        "patient_id": patient_id
    }

# ===== PHARMACY TOOLS =====

@mcp.tool()
@traced_tool
def pharmacy_request(medication_type: str, lat: float, lon: float) -> dict:
    """Check pharmacy stock and approve prescription"""
    nearby_pharmacies = [
        {"name": "Sehat Pharmacy", "lat": 31.5204, "lon": 74.3587, "available": True},
        {"name": "HealthPlus", "lat": 31.5400, "lon": 74.3600, "available": True}
    ]
    nearest = min(nearby_pharmacies, key=lambda p: haversine(lat, lon, p["lat"], p["lon"]))
    return {
        "status": "approved" if nearest["available"] else "unavailable",
        "medication": medication_type,
        "pharmacy": nearest["name"],
        "prescription_id": f"RX-{random.randint(10000, 99999)}"
    }


@mcp.tool()
@traced_tool
def maternal_pharmacy_handoff(lat: float, lon: float, medication_type: str, mother_id: str) -> dict:
    """Pharmacy handoff for supplements"""
    response = pharmacy_request(medication_type, lat, lon)
    response["mother_id"] = mother_id
    return response


@mcp.tool()
@traced_tool
def check_pharmacy_stock(site_id: str, medicine: str) -> dict:
    """Check medicine stock at specific facility"""
    stock_levels = {
        "site_LHR_001": {"iron_supplement": 200, "amoxicillin": 120, "paracetamol": 500},
        "site_LHR_002": {"iron_supplement": 50, "amoxicillin": 5, "paracetamol": 300}
    }
    count = stock_levels.get(site_id, {}).get(medicine, 0)
    return {
        "site_id": site_id,
        "medicine": medicine,
        "count": count,
        "status": "critical" if count < 50 else "low" if count < 100 else "ok"
    }


@mcp.tool()
@traced_tool
def predict_medicine_shortage(medicine: str) -> dict:
    """Predict shortage across all facilities"""
    total = random.randint(50, 500)
    if total < 100:
        risk = "critical"
        days = 3
    elif total < 250:
        risk = "warning"
        days = 10
    else:
        risk = "ok"
        days = 30
    return {
        "medicine": medicine,
        "total_stock": total,
        "risk_level": risk,
        "days_remaining": days
    }


@mcp.tool()
@traced_tool
def generate_purchase_order(medicine: str, quantity: int, site_id: str) -> dict:
    """Auto-generate purchase order"""
    po_id = f"PO-{random.randint(10000, 99999)}"
    return {
        "status": "created",
        "po_id": po_id,
        "medicine": medicine,
        "quantity": quantity,
        "site_id": site_id,
        "estimated_delivery_days": 5
    }


@mcp.tool()
@traced_tool
def reallocate_medicine(from_site: str, to_site: str, medicine: str, quantity: int) -> dict:
    """Reallocate stock between facilities"""
    return {
        "status": "reallocated",
        "from_site": from_site,
        "to_site": to_site,
        "medicine": medicine,
        "quantity": quantity,
        "completion_time": "2 hours"
    }


@mcp.tool()
@traced_tool
def create_patient_prescription(patient_id: str, medicine: str, dosage: str, duration_days: int) -> dict:
    """Create prescription for patient"""
    rx_id = f"RX-{random.randint(10000, 99999)}"
    return {
        "status": "created",
        "rx_id": rx_id,
        "patient_id": patient_id,
        "medicine": medicine,
        "dosage": dosage,
        "duration_days": duration_days
    }


@mcp.tool()
@traced_tool
def detect_abnormal_consumption(medicine: str, patient_id: str, daily_usage: int) -> dict:
    """Detect potential medicine abuse"""
    normal_range = {"paracetamol": 3, "amoxicillin": 3, "iron_supplement": 2}
    max_allowed = normal_range.get(medicine, 3)
    if daily_usage > max_allowed * 2:
        flag = "high_risk_abuse"
    elif daily_usage > max_allowed:
        flag = "suspicious"
    else:
        flag = "normal"
    return {
        "patient_id": patient_id,
        "medicine": medicine,
        "daily_usage": daily_usage,
        "max_allowed": max_allowed,
        "flag": flag
    }


# ===== MENTAL HEALTH TOOLS =====

@mcp.tool()
@traced_tool
def assess_stress_level(symptoms: str, duration_days: int) -> dict:
    """AI-based stress assessment"""
    score = random.randint(1, 10)
    level = "high" if score > 7 else "moderate" if score > 4 else "low"
    return {"stress_score": score, "stress_level": level, "advice": f"Detected {level} stress — consider follow-up."}


@mcp.tool()
@traced_tool
def assign_therapist(patient_id: str, issue_type: str) -> dict:
    """Assign nearest or most relevant therapist"""
    therapists = [
        {"name": "Dr. Ayesha Raza", "specialty": "Anxiety"},
        {"name": "Dr. Farhan Qureshi", "specialty": "Depression"},
        {"name": "Dr. Nida Shah", "specialty": "Trauma"}
    ]
    chosen = random.choice(therapists)
    return {
        "status": "assigned",
        "patient_id": patient_id,
        "therapist": chosen["name"],
        "specialty": chosen["specialty"],
        "session_id": f"TH-{random.randint(1000, 9999)}"
    }


@mcp.tool()
@traced_tool
def schedule_followup(patient_id: str, days_from_now: int = 7) -> dict:
    """Schedule follow-up therapy session"""
    followup_time = time.time() + days_from_now * 86400
    return {
        "patient_id": patient_id,
        "followup_timestamp": followup_time,
        "days_until_followup": days_from_now,
        "status": "scheduled"
    }


@mcp.tool()
@traced_tool
def mental_emergency_hotline(lat: float, lon: float, emergency_desc: str) -> dict:
    """Emergency mental health hotline dispatch"""
    responders = [
        {"org": "MindRelief Helpline", "contact": "0800-111-222"},
        {"org": "PsychAid Emergency", "contact": "0800-777-888"}
    ]
    chosen = random.choice(responders)
    return {
        "status": "connected",
        "organization": chosen["org"],
        "contact": chosen["contact"],
        "message": f"Emergency response initiated for: {emergency_desc}"
    }


# ===== RESEARCH AGENT TOOLS =====

RESEARCH_SENDER_EMAIL = "nooreasal786@gmail.com"
APP_PASSWORD = "irph tole tuqr vfmi"

UNIVERSITIES = [
    {"name": "University of Health Sciences", "oric_email": "hafizalaibafaisal@gmail.com"},
    {"name": "King Edward Medical University", "oric_email": "jiniewinie000@gmail.com"},
    {"name": "Lahore Medical College", "oric_email": "ismatabubakar6@gmail.com"},
]


@mcp.tool()
@traced_tool
def aggregate_hospital_data() -> dict:
    """Aggregate hospital data for research"""
    mongo_client, db = get_mongo()
    if not mongo_client:
        return {"error": "MongoDB unavailable", "trends": {}}

    trends = {
        "Cardiac_patients": random.randint(300, 600),
        "Maternal_patients": random.randint(200, 500),
        "Mental_patients": random.randint(100, 300)
    }
    return {"trends": trends, "timestamp": time.time()}


@mcp.tool()
@traced_tool
def detect_high_demand_fields() -> dict:
    """Detect high-demand healthcare fields"""
    data = aggregate_hospital_data()["trends"]
    high_demand = [k for k, v in data.items() if v > 300]
    return {"high_demand_fields": high_demand}


@mcp.tool()
@traced_tool
def assign_internships() -> dict:
    """Assign internships based on demand"""
    fields = detect_high_demand_fields()["high_demand_fields"]
    assignments = [
        {"student": "Ali Raza", "department": "MBBS", "field": fields[0] if fields else "Cardiology"}
    ]
    return {"assignments": assignments}


@mcp.tool()
@traced_tool
def send_university_email(topic: str, content: str) -> dict:
    """Send emails to universities"""
    EmailMessage, smtplib, threading = get_email()

    results = []

    def send_email(uni):
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Research Proposal: {topic}"
            msg['From'] = RESEARCH_SENDER_EMAIL
            msg['To'] = uni["oric_email"]
            msg.set_content(content)

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(RESEARCH_SENDER_EMAIL, APP_PASSWORD)
                smtp.send_message(msg)

            results.append({"university": uni["name"], "status": "sent"})
        except Exception as e:
            results.append({"university": uni["name"], "status": "failed", "error": str(e)})

    threads = [threading.Thread(target=send_email, args=(uni,)) for uni in UNIVERSITIES]
    for t in threads: t.start()
    for t in threads: t.join()

    return {"emails": results}


# ===== CRIMINAL CASE TOOLS =====

@mcp.tool()
@traced_tool
def classify_injury_local(injury_notes: str, injury_type: str) -> dict:
    """Local AI-powered injury classification"""
    violence_keywords = [
        "assault", "attack", "beaten", "hit", "struck", "kicked",
        "knife", "blade", "sharp", "stab", "cut", "slash",
        "gunshot", "bullet", "firearm"
    ]

    harassment_keywords = [
        "rape", "sexual assault", "molestation", "harassment",
        "domestic violence", "domestic abuse"
    ]

    injury_lower = injury_notes.lower()
    violence_score = sum(1 for keyword in violence_keywords if keyword in injury_lower)
    harassment_score = sum(1 for keyword in harassment_keywords if keyword in injury_lower)

    if harassment_score > 0:
        classification = "sexual_violence_or_harassment"
        severity = "critical"
        auto_report = True
    elif violence_score >= 3:
        classification = "suspicious_violence"
        severity = "high"
        auto_report = True
    elif violence_score >= 1:
        classification = "potential_violence"
        severity = "moderate"
        auto_report = True
    else:
        classification = "non_suspicious"
        severity = "low"
        auto_report = False

    return {
        "classification": classification,
        "severity": severity,
        "auto_report_required": auto_report,
        "violence_score": violence_score,
        "harassment_score": harassment_score
    }


@mcp.tool()
@traced_tool
def create_case_report(patient_id: str, injury_notes: str, injury_type: str, location: str,
                       cnic: str = None, victim_name: str = None) -> dict:
    """Create criminal case report"""
    case_id = f"CASE-{random.randint(10000, 99999)}"
    classification_result = classify_injury_local(injury_notes, injury_type)

    police_jurisdictions = {
        "Gulberg": {"station": "Civil Lines Police Station", "contact": "+92423456789"},
        "Model Town": {"station": "Civil Lines Police Station", "contact": "+92423456789"},
        "Cantt": {"station": "Cantonment Police Station", "contact": "+92423456790"}
    }

    jurisdiction = police_jurisdictions.get("Gulberg")
    for area, details in police_jurisdictions.items():
        if area.lower() in location.lower():
            jurisdiction = details
            break

    return {
        "case_id": case_id,
        "patient_id": patient_id,
        "victim_name": "REDACTED_FOR_PRIVACY" if victim_name else None,
        "cnic": "REDACTED_FOR_PRIVACY" if cnic else None,
        "injury_type": injury_type,
        "injury_notes": injury_notes,
        "location": location,
        "classification": classification_result["classification"],
        "severity": classification_result["severity"],
        "auto_report_required": classification_result["auto_report_required"],
        "police_station": jurisdiction["station"],
        "police_contact": jurisdiction["contact"],
        "status": "pending_review",
        "created_at": time.time()
    }


@mcp.tool()
@traced_tool
def report_to_police(case_id: str, case_data: dict) -> dict:
    """Auto-report suspicious case to police"""
    if not case_data.get("auto_report_required", False):
        return {
            "status": "skipped",
            "message": "Case does not require auto-report",
            "case_id": case_id
        }

    report_id = f"POLICE-{random.randint(10000, 99999)}"

    return {
        "status": "reported",
        "case_id": case_id,
        "report_id": report_id,
        "police_station": case_data["police_station"],
        "police_contact": case_data["police_contact"],
        "reported_at": time.time()
    }


@mcp.tool()
@traced_tool
def verify_identity_nadra(cnic: str) -> dict:
    """Verify identity via NADRA"""
    if not cnic or len(cnic) != 15:
        return {"status": "failed", "message": "Invalid CNIC format"}

    verified = random.choice([True, True, True, False])

    if verified:
        return {
            "status": "verified",
            "cnic_last_4": cnic[-4:],
            "name": "REDACTED_FOR_PRIVACY",
            "verified_at": time.time(),
            "nadra_reference": f"NADRA-{random.randint(1000000, 9999999)}"
        }
    else:
        return {
            "status": "not_found",
            "cnic_last_4": cnic[-4:],
            "message": "CNIC not found in NADRA database"
        }

@mcp.tool()
@traced_tool
def collect_medical_evidence(case_id: str, evidence_type: str, evidence_notes: str) -> dict:
    """Collect medical evidence for criminal cases"""
    evidence_id = f"EVD-{random.randint(10000, 99999)}"

    # Evidence severity classification
    critical_keywords = ["fracture", "deep cut", "gunshot", "penetrating injury", "severe bleeding"]
    moderate_keywords = ["bruise", "swelling", "abrasion", "minor cut"]

    notes_lower = evidence_notes.lower()

    severity = "low"
    if any(word in notes_lower for word in critical_keywords):
        severity = "critical"
    elif any(word in notes_lower for word in moderate_keywords):
        severity = "moderate"

    return {
        "status": "collected",
        "case_id": case_id,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "evidence_notes": evidence_notes,
        "severity": severity,
        "collected_at": time.time()
    }

@mcp.tool()
@traced_tool
def transfer_evidence_to_forensics(evidence_id: str, case_id: str) -> dict:
    """Transfer medical evidence to forensics"""
    forensic_reference = f"FORENSIC-{random.randint(10000, 99999)}"

    return {
        "status": "transferred",
        "evidence_id": evidence_id,
        "case_id": case_id,
        "forensics_reference": forensic_reference,
        "transferred_at": time.time(),
        "expected_report_days": random.randint(7, 21)
    }


# ===== WASTE MANAGEMENT TOOLS =====

@mcp.tool()
@traced_tool
def monitor_container_levels() -> dict:
    """Monitor all container levels"""
    containers = {
        "CONT-001": {
            "container_id": "CONT-001",
            "location": "Services Hospital - Emergency Wing",
            "waste_type": "bio_medical",
            "current_level_percent": 45.0,
            "sensor_status": "active"
        },
        "CONT-002": {
            "container_id": "CONT-002",
            "location": "Mayo Hospital - Surgery Ward",
            "waste_type": "bio_medical",
            "current_level_percent": 85.0,
            "sensor_status": "active"
        },
        "CONT-003": {
            "container_id": "CONT-003",
            "location": "Jinnah Hospital - ICU",
            "waste_type": "bio_medical",
            "current_level_percent": 92.0,
            "sensor_status": "active"
        }
    }

    critical_containers = [c for c in containers.values() if c["current_level_percent"] >= 90]

    return {
        "total_containers": len(containers),
        "all_containers": containers,
        "critical": critical_containers,
        "critical_count": len(critical_containers),
        "monitoring_timestamp": time.time()
    }


@mcp.tool()
@traced_tool
def schedule_pickup(container_id: str, priority: str = "normal") -> dict:
    """Schedule automatic pickup"""
    containers = {
        "CONT-001": {"location": "Services Hospital", "waste_type": "bio_medical"},
        "CONT-002": {"location": "Mayo Hospital", "waste_type": "bio_medical"},
        "CONT-003": {"location": "Jinnah Hospital", "waste_type": "bio_medical"}
    }

    if container_id not in containers:
        return {"status": "error", "message": "Container not found"}

    pickup_id = f"PICKUP-{random.randint(10000, 99999)}"
    eta_hours = 2 if priority == "urgent" else 6

    return {
        "status": "scheduled",
        "pickup_id": pickup_id,
        "container_id": container_id,
        "location": containers[container_id]["location"],
        "priority": priority,
        "eta_hours": eta_hours,
        "scheduled_time": time.time() + (eta_hours * 3600)
    }


@mcp.tool()
@traced_tool
def optimize_collection_route(depot_location: str = "Lahore Depot") -> dict:
    """Optimize routing for garbage collection trucks"""
    containers = [
        {"container_id": "CONT-002", "location": "Mayo Hospital", "level": 85.0},
        {"container_id": "CONT-003", "location": "Jinnah Hospital", "level": 92.0}
    ]

    route_id = f"ROUTE-{random.randint(10000, 99999)}"

    return {
        "status": "optimized",
        "route_id": route_id,
        "depot": depot_location,
        "total_stops": len(containers),
        "route_stops": containers,
        "total_distance_km": 15.5,
        "estimated_time_hours": 2.5
    }


@mcp.tool()
@traced_tool
def handle_pharmaceutical_waste(container_id: str) -> dict:
    """Special handling for pharmaceutical waste"""
    disposal_id = f"PHARMA-DISP-{random.randint(10000, 99999)}"

    return {
        "status": "scheduled",
        "disposal_id": disposal_id,
        "container_id": container_id,
        "disposal_method": "Incineration at authorized facility",
        "facility": "Punjab Pharmaceutical Waste Treatment Plant",
        "scheduled_time": time.time() + (24 * 3600)
    }


@mcp.tool()
@traced_tool
def sync_with_lwmc(data_type: str = "all") -> dict:
    """Sync waste management data with LWMC"""
    sync_id = f"LWMC-{random.randint(10000, 99999)}"

    return {
        "status": "success",
        "sync_id": sync_id,
        "data_type": data_type,
        "sync_time": time.time(),
        "lwmc_confirmed": True,
        "total_records_synced": random.randint(10, 50)
    }


# ===== RESOURCES =====

@mcp.resource("trace://dispatch/last")
def last_dispatch():
    """Get last dispatch record"""
    return LAST_DISPATCH_LOG[-1] if LAST_DISPATCH_LOG else {}


@mcp.resource("trace://mental/last")
def last_mental_case():
    """Last mental health case"""
    return {"info": "Last recorded mental case trace (mock)"}


def debug_log(msg):
    print(msg, file=sys.stderr, flush=True)


mcp = FastMCP("Criminal Forensics Agent")
debug_log("✅ Criminal MCP initialized")

# ===== DATA FILES =====
CASES_FILE = "criminal_cases.json"
EVIDENCE_FILE = "criminal_evidence.json"
FOLLOWUPS_FILE = "criminal_followups.json"


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []


def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


# ===== TRACE LOG =====
TRACE_LOG = []


def log_trace(action: str, details: dict):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    TRACE_LOG.append(entry)
    debug_log(f"[TRACE] {action}: {str(details)[:100]}")


def traced_tool(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        call_id = f"{func.__name__}-{int(time.time() * 1000)}"
        log_trace("tool_call_start", {
            "tool": func.__name__,
            "call_id": call_id
        })
        try:
            result = func(*args, **kwargs)
            log_trace("tool_call_end", {
                "tool": func.__name__,
                "call_id": call_id,
                "status": "success"
            })
            return result
        except Exception as e:
            log_trace("tool_call_error", {
                "tool": func.__name__,
                "call_id": call_id,
                "error": str(e)
            })
            raise

    return wrapper


# ===== POLICE JURISDICTIONS =====
POLICE_JURISDICTIONS = {
    "Lahore_City": {
        "station_name": "Civil Lines Police Station",
        "contact": "+92423456789",
        "email": "hafizalaibafaisal@gmail.com",
        "jurisdiction": ["Gulberg", "Model Town", "Garden Town"]
    },
    "Lahore_Cantt": {
        "station_name": "Cantonment Police Station",
        "contact": "+92423456790",
        "email": "jiniewinie000@gmail.com",
        "jurisdiction": ["Cantt", "Mall Road", "Cavalry Ground"]
    },
    "Lahore_Iqbal": {
        "station_name": "Iqbal Town Police Station",
        "contact": "+92423456791",
        "email": "ismatabubakar6@gmail.com",
        "jurisdiction": ["Iqbal Town", "Johar Town", "Wapda Town"]
    }
}


def get_jurisdiction(location_area):
    for jurisdiction_id, details in POLICE_JURISDICTIONS.items():
        if any(area.lower() in location_area.lower() for area in details["jurisdiction"]):
            return jurisdiction_id, details
    return "Lahore_City", POLICE_JURISDICTIONS["Lahore_City"]


# ===== CRIMINAL CASE TOOLS =====

@mcp.tool()
@traced_tool
def classify_injury_local(injury_notes: str, injury_type: str) -> dict:
    """AI-powered injury classification - detects violence, harassment, abuse"""
    violence_keywords = [
        "assault", "attack", "beaten", "hit", "struck", "kicked", "mara", "pitai",
        "knife", "blade", "sharp", "stab", "cut", "slash", "chaku",
        "gunshot", "bullet", "firearm", "goli"
    ]

    harassment_keywords = [
        "rape", "sexual assault", "molestation", "harassment", "ziadti",
        "domestic violence", "domestic abuse", "ghar ka jhagra"
    ]

    injury_lower = injury_notes.lower()
    violence_score = sum(1 for kw in violence_keywords if kw in injury_lower)
    harassment_score = sum(1 for kw in harassment_keywords if kw in injury_lower)

    if harassment_score > 0:
        classification = "sexual_violence_or_harassment"
        severity = "critical"
        auto_report = True
    elif violence_score >= 3:
        classification = "suspicious_violence"
        severity = "high"
        auto_report = True
    elif violence_score >= 1:
        classification = "potential_violence"
        severity = "moderate"
        auto_report = True
    else:
        classification = "non_suspicious"
        severity = "low"
        auto_report = False

    return {
        "classification": classification,
        "severity": severity,
        "auto_report_required": auto_report,
        "violence_score": violence_score,
        "harassment_score": harassment_score
    }


@mcp.tool()
@traced_tool
def create_case_report(patient_id: str, injury_notes: str, injury_type: str,
                       location: str, cnic: str = None, victim_name: str = None) -> dict:
    """Create criminal case report with privacy protection"""
    case_id = f"CASE-{random.randint(10000, 99999)}"
    classification_result = classify_injury_local(injury_notes, injury_type)

    jurisdiction_id, jurisdiction = get_jurisdiction(location)

    case_data = {
        "case_id": case_id,
        "patient_id": patient_id,
        "victim_name": "REDACTED_FOR_PRIVACY" if victim_name else None,
        "cnic": "REDACTED_FOR_PRIVACY" if cnic else None,
        "injury_type": injury_type,
        "injury_notes": injury_notes,
        "location": location,
        "classification": classification_result["classification"],
        "severity": classification_result["severity"],
        "auto_report_required": classification_result["auto_report_required"],
        "police_station": jurisdiction["station_name"],
        "police_contact": jurisdiction["contact"],
        "police_email": jurisdiction["email"],
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "followup_due_date": (datetime.now() + timedelta(days=180)).isoformat()  # 6 months
    }

    # Save case
    cases = load_json(CASES_FILE)
    cases.append(case_data)
    save_json(CASES_FILE, cases)

    return case_data


@mcp.tool()
@traced_tool
def report_to_police(case_id: str, case_data: dict) -> dict:
    """Auto-report suspicious case to police via email"""
    if not case_data.get("auto_report_required", False):
        return {
            "status": "skipped",
            "message": "Case does not require auto-report",
            "case_id": case_id
        }

    report_id = f"POLICE-{random.randint(10000, 99999)}"

    # Mock email send (in production, use SMTP)
    debug_log(f"📧 EMAIL SENT: {case_data['police_email']}")
    debug_log(f"Subject: URGENT CRIMINAL CASE REPORT - {case_id}")
    debug_log(f"Body: Case detected at {case_data['location']}, severity: {case_data['severity']}")

    return {
        "status": "reported",
        "case_id": case_id,
        "report_id": report_id,
        "police_station": case_data["police_station"],
        "police_email": case_data["police_email"],
        "reported_at": datetime.now().isoformat()
    }


@mcp.tool()
@traced_tool
def verify_identity_nadra(cnic: str) -> dict:
    """Verify identity via NADRA"""
    if not cnic or len(cnic) != 15:
        return {"status": "failed", "message": "Invalid CNIC format"}

    verified = random.choice([True, True, True, False])

    if verified:
        return {
            "status": "verified",
            "cnic_last_4": cnic[-4:],
            "name": "REDACTED_FOR_PRIVACY",
            "verified_at": datetime.now().isoformat(),
            "nadra_reference": f"NADRA-{random.randint(1000000, 9999999)}"
        }
    else:
        return {
            "status": "not_found",
            "cnic_last_4": cnic[-4:],
            "message": "CNIC not found in NADRA database"
        }


@mcp.tool()
@traced_tool
def collect_medical_evidence(case_id: str, evidence_type: str, evidence_notes: str) -> dict:
    """Collect medical evidence for criminal cases"""
    evidence_id = f"EVD-{random.randint(10000, 99999)}"

    critical_keywords = ["fracture", "deep cut", "gunshot", "penetrating injury", "severe bleeding"]
    moderate_keywords = ["bruise", "swelling", "abrasion", "minor cut"]

    notes_lower = evidence_notes.lower()

    severity = "low"
    if any(word in notes_lower for word in critical_keywords):
        severity = "critical"
    elif any(word in notes_lower for word in moderate_keywords):
        severity = "moderate"

    evidence_data = {
        "evidence_id": evidence_id,
        "case_id": case_id,
        "evidence_type": evidence_type,
        "evidence_notes": evidence_notes,
        "severity": severity,
        "collected_at": datetime.now().isoformat(),
        "chain_of_custody": [
            {
                "handler": "Hospital Staff",
                "timestamp": datetime.now().isoformat(),
                "action": "Collected"
            }
        ]
    }

    # Save evidence
    evidence_list = load_json(EVIDENCE_FILE)
    evidence_list.append(evidence_data)
    save_json(EVIDENCE_FILE, evidence_list)

    return evidence_data


@mcp.tool()
@traced_tool
def transfer_evidence_to_forensics(evidence_id: str, case_id: str) -> dict:
    """Transfer medical evidence to forensics with chain of custody"""
    forensic_reference = f"FORENSIC-{random.randint(10000, 99999)}"

    # Update chain of custody
    evidence_list = load_json(EVIDENCE_FILE)
    for evidence in evidence_list:
        if evidence["evidence_id"] == evidence_id:
            evidence["chain_of_custody"].append({
                "handler": "Forensics Department",
                "timestamp": datetime.now().isoformat(),
                "action": "Transferred"
            })
            break
    save_json(EVIDENCE_FILE, evidence_list)

    return {
        "status": "transferred",
        "evidence_id": evidence_id,
        "case_id": case_id,
        "forensics_reference": forensic_reference,
        "transferred_at": datetime.now().isoformat(),
        "expected_report_days": random.randint(7, 21)
    }


@mcp.tool()
@traced_tool
def get_police_jurisdiction(location: str) -> dict:
    """Get police jurisdiction for a location"""
    jurisdiction_id, jurisdiction = get_jurisdiction(location)
    return {
        "jurisdiction_id": jurisdiction_id,
        "station_name": jurisdiction["station_name"],
        "contact": jurisdiction["contact"],
        "email": jurisdiction["email"],
        "jurisdiction_areas": jurisdiction["jurisdiction"]
    }


@mcp.tool()
@traced_tool
def pseudonymize_case_data(case_data: dict) -> dict:
    """Pseudonymize sensitive case data before external sharing"""
    pseudonymized = case_data.copy()

    if "victim_name" in pseudonymized:
        pseudonymized["victim_name"] = "REDACTED_VICTIM_NAME"
    if "cnic" in pseudonymized:
        pseudonymized["cnic"] = "REDACTED_CNIC"
    if "phone" in pseudonymized:
        pseudonymized["phone"] = "REDACTED_PHONE"
    if "address" in pseudonymized:
        pseudonymized["address"] = "REDACTED_ADDRESS"

    return pseudonymized


# ===== NEW: 6-MONTH FOLLOW-UP TOOLS =====

@mcp.tool()
@traced_tool
def schedule_followup(case_id: str, followup_date: str = None, followup_type: str = "case_status_check") -> dict:
    """Schedule 6-month follow-up for case closure verification"""

    if not followup_date:
        followup_date = (datetime.now() + timedelta(days=180)).isoformat()

    followup_id = f"FOLLOWUP-{random.randint(10000, 99999)}"

    followup_data = {
        "followup_id": followup_id,
        "case_id": case_id,
        "followup_type": followup_type,
        "scheduled_date": followup_date,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "reminder_sent": False
    }

    # Save follow-up
    followups = load_json(FOLLOWUPS_FILE)
    followups.append(followup_data)
    save_json(FOLLOWUPS_FILE, followups)

    return followup_data


@mcp.tool()
@traced_tool
def check_pending_followups() -> dict:
    """Check for pending follow-ups that are due"""
    followups = load_json(FOLLOWUPS_FILE)
    now = datetime.now()

    pending = []
    for followup in followups:
        if followup["status"] == "pending":
            followup_date = datetime.fromisoformat(followup["scheduled_date"])
            if followup_date <= now:
                pending.append(followup)

    return {
        "total_pending": len(pending),
        "due_followups": pending
    }


@mcp.tool()
@traced_tool
def update_case_status(case_id: str, new_status: str, closure_notes: str = None) -> dict:
    """Update case status (open, closed, reopened)"""
    cases = load_json(CASES_FILE)

    case_found = False
    for case in cases:
        if case["case_id"] == case_id:
            case["status"] = new_status
            case["updated_at"] = datetime.now().isoformat()
            if closure_notes:
                case["closure_notes"] = closure_notes
            if new_status == "closed":
                case["closed_at"] = datetime.now().isoformat()
            case_found = True
            break

    if case_found:
        save_json(CASES_FILE, cases)
        return {
            "status": "updated",
            "case_id": case_id,
            "new_status": new_status,
            "updated_at": datetime.now().isoformat()
        }
    else:
        return {
            "status": "error",
            "message": "Case not found"
        }


@mcp.tool()
@traced_tool
def generate_followup_report(case_id: str) -> dict:
    """Generate comprehensive follow-up report for a case"""
    cases = load_json(CASES_FILE)
    evidence_list = load_json(EVIDENCE_FILE)
    followups = load_json(FOLLOWUPS_FILE)

    case_data = None
    for case in cases:
        if case["case_id"] == case_id:
            case_data = case
            break

    if not case_data:
        return {"status": "error", "message": "Case not found"}

    # Get evidence for this case
    case_evidence = [e for e in evidence_list if e["case_id"] == case_id]

    # Get follow-ups for this case
    case_followups = [f for f in followups if f["case_id"] == case_id]

    # Calculate duration
    created_at = datetime.fromisoformat(case_data["created_at"])
    duration_days = (datetime.now() - created_at).days

    report = {
        "case_id": case_id,
        "case_status": case_data["status"],
        "classification": case_data["classification"],
        "severity": case_data["severity"],
        "created_at": case_data["created_at"],
        "duration_days": duration_days,
        "police_station": case_data["police_station"],
        "total_evidence_collected": len(case_evidence),
        "evidence_items": case_evidence,
        "total_followups": len(case_followups),
        "followup_history": case_followups,
        "closure_status": "case_open" if case_data["status"] == "open" else "case_closed",
        "report_generated_at": datetime.now().isoformat()
    }

    return report


@mcp.tool()
@traced_tool
def send_followup_reminder(case_id: str, recipient_email: str) -> dict:
    """Send follow-up reminder email to police/hospital"""

    report = generate_followup_report(case_id)

    # Mock email send
    debug_log(f"📧 FOLLOWUP EMAIL SENT: {recipient_email}")
    debug_log(f"Subject: 6-MONTH CASE FOLLOW-UP - {case_id}")
    debug_log(f"Duration: {report['duration_days']} days")
    debug_log(f"Status: {report['case_status']}")

    # Update followup record
    followups = load_json(FOLLOWUPS_FILE)
    for followup in followups:
        if followup["case_id"] == case_id and followup["status"] == "pending":
            followup["reminder_sent"] = True
            followup["reminder_sent_at"] = datetime.now().isoformat()
            break
    save_json(FOLLOWUPS_FILE, followups)

    return {
        "status": "sent",
        "case_id": case_id,
        "recipient": recipient_email,
        "sent_at": datetime.now().isoformat()
    }


@mcp.tool()
@traced_tool
def check_case_closure_status(case_id: str) -> dict:
    """Check if case is still open after 6 months"""
    cases = load_json(CASES_FILE)

    for case in cases:
        if case["case_id"] == case_id:
            created_at = datetime.fromisoformat(case["created_at"])
            duration_days = (datetime.now() - created_at).days

            if duration_days >= 180 and case["status"] == "open":
                return {
                    "case_id": case_id,
                    "status": "open",
                    "duration_days": duration_days,
                    "action_required": "send_followup_reminder",
                    "message": "Case is still open after 6 months - follow-up needed"
                }
            elif case["status"] == "closed":
                return {
                    "case_id": case_id,
                    "status": "closed",
                    "closed_at": case.get("closed_at"),
                    "message": "Case closed successfully"
                }
            else:
                return {
                    "case_id": case_id,
                    "status": "open",
                    "duration_days": duration_days,
                    "message": "Case is within 6-month monitoring period"
                }

    return {"status": "error", "message": "Case not found"}


# ===== RESOURCES =====
@mcp.resource("trace://criminal/last")
def last_criminal_case():
    """Get last criminal case trace"""
    return TRACE_LOG[-1] if TRACE_LOG else {}


# ===== WASTE MANAGEMENT TOOLS (NEW) =====

@mcp.tool()
@traced_tool
def analyze_video_waste(video_path: str) -> dict:
    """Analyze hospital waste video using AI detection (DUMMY DATA FOR NOW)"""

    import random
    from pathlib import Path

    debug_log(f"🎬 Analyzing video: {video_path}")

    # Check if video exists
    video_file = Path(video_path)
    if not video_file.exists():
        return {
            "error": f"Video file not found: {video_path}",
            "status": "failed"
        }

    # Generate dummy analysis (real models load karne ki zaroorat nahi)
    placenta_detected = random.choice([True, True, False])
    placenta_kg = round(random.uniform(2, 8), 1) if placenta_detected else 0

    analysis = {
        "video_path": video_path,
        "analysis_timestamp": datetime.now().isoformat(),
        "duration_seconds": random.randint(120, 300),
        "models_used": ["Placenta Detector v2.1 (DEMO)", "Waste Classifier v1.8 (DEMO)"],
        "waste_detected": {
            "bio_medical": round(random.uniform(10, 25), 1),
            "sharps": round(random.uniform(2, 6), 1),
            "pharmaceutical": round(random.uniform(0, 5), 1),
            "placenta": placenta_kg,
            "general": round(random.uniform(5, 15), 1)
        },
        "violations": [],
        "confidence_scores": {
            "placenta_detection": 0.94 if placenta_detected else None,
            "waste_classification": 0.91
        }
    }

    # Add violations randomly
    if random.random() > 0.6:
        analysis["violations"].append({
            "type": "waste_mixing",
            "timestamp": "00:45",
            "description": "Bio-medical waste mixed with general waste",
            "severity": "high"
        })

    debug_log(f"✅ Analysis complete: {placenta_kg}kg placenta, {analysis['waste_detected']['bio_medical']}kg bio-waste")

    return analysis


@mcp.tool()
@traced_tool
def find_disposal_companies(waste_type: str, location: str = "Lahore") -> dict:
    """Find disposal companies for waste type"""

    companies = [
        {
            "id": "COMP-001",
            "name": "LWMC (Lahore Waste Management)",
            "price_per_kg": 75 if waste_type == "bio_medical" else 85 if waste_type == "sharps" else 150,
            "epa_certified": True,
            "rating": 4.2
        },
        {
            "id": "COMP-002",
            "name": "EcoWaste Solutions",
            "price_per_kg": 68 if waste_type == "bio_medical" else 80 if waste_type == "sharps" else 140,
            "epa_certified": True,
            "rating": 4.7
        },
        {
            "id": "COMP-003",
            "name": "GreenMed Disposal",
            "price_per_kg": 80 if waste_type == "bio_medical" else 90 if waste_type == "sharps" else 160,
            "epa_certified": True,
            "rating": 4.0
        }
    ]

    return {
        "waste_type": waste_type,
        "location": location,
        "companies_found": len(companies),
        "companies": companies
    }


@mcp.tool()
@traced_tool
def calculate_disposal_cost(waste_breakdown: dict, company_id: str = "COMP-002") -> dict:
    """Calculate total disposal cost"""

    pricing = {
        "COMP-001": {"bio_medical": 75, "sharps": 85, "placenta": 150, "general": 15},
        "COMP-002": {"bio_medical": 68, "sharps": 80, "placenta": 140, "general": 12},
        "COMP-003": {"bio_medical": 80, "sharps": 90, "placenta": 160, "general": 18}
    }

    company_pricing = pricing.get(company_id, pricing["COMP-002"])

    total_cost = 0
    cost_details = []

    for waste_type, quantity in waste_breakdown.items():
        if quantity > 0:
            price_per_kg = company_pricing.get(waste_type, 50)
            cost = price_per_kg * quantity
            total_cost += cost

            cost_details.append({
                "waste_type": waste_type,
                "quantity_kg": quantity,
                "price_per_kg": price_per_kg,
                "subtotal": round(cost, 2)
            })

    return {
        "company_id": company_id,
        "company_name": "EcoWaste Solutions" if company_id == "COMP-002" else "LWMC",
        "cost_breakdown": cost_details,
        "total_cost": round(total_cost, 2),
        "currency": "PKR"
    }


@mcp.tool()
@traced_tool
def schedule_waste_pickup(hospital_id: str, company_id: str, pickup_time: str, waste_kg: float) -> dict:
    """Schedule waste pickup"""

    pickup_id = f"PICKUP-{random.randint(10000, 99999)}"

    return {
        "status": "scheduled",
        "pickup_id": pickup_id,
        "hospital_id": hospital_id,
        "company_id": company_id,
        "company_name": "EcoWaste Solutions",
        "pickup_time": pickup_time,
        "waste_kg": waste_kg,
        "truck_id": f"BIO-HAZARD-{random.randint(100, 999)}",
        "driver_name": random.choice(["Ahmed Khan", "Ali Raza", "Usman Sheikh"]),
        "driver_contact": "0300-" + str(random.randint(1000000, 9999999)),
        "scheduled_at": datetime.now().isoformat()
    }
# ===== RUN SERVER =====
if __name__ == "__main__":
    debug_log("🚀 Starting agents_mcp.py...")
    mcp.run()
