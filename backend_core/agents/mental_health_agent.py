# # mental_agent.py - Complete Mental Health Agent
# import asyncio
# import json
# import os
# import re
# import smtplib
# from datetime import datetime, timedelta
# from email.message import EmailMessage
# from openai import AsyncOpenAI
# from agents import Agent, Runner, OpenAIChatCompletionsModel
# from agents.mcp import MCPServerStdio
#
# # ===== LOAD ENV =====
# from dotenv import load_dotenv
# load_dotenv()
# # ===== GEMINI SETUP =====
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#
# if not GEMINI_API_KEY:
#     raise ValueError("❌ GEMINI_API_KEY not found in .env file!")
#
# client = AsyncOpenAI(
#     api_key=GEMINI_API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )
#
# gemini_model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=client
# )
#
# # ===== EMAIL CONFIG =====
# SENDER_EMAIL = "nooreasal786@gmail.com"
# APP_PASSWORD = "irph tole tuqr vfmi"
#
# def send_email_notification(receiver_email, subject, body):
#     """📧 Email notification"""
#     try:
#         msg = EmailMessage()
#         msg['Subject'] = subject
#         msg['From'] = SENDER_EMAIL
#         msg['To'] = receiver_email
#         msg.set_content(body)
#
#         with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
#             smtp.starttls()
#             smtp.login(SENDER_EMAIL, APP_PASSWORD)
#             smtp.send_message(msg)
#
#         print(f"✉️ Email sent to {receiver_email}")
#         return True
#     except Exception as e:
#         print(f"❌ Email failed: {e}")
#         return False
#
# # ===== AUDIT LOGS =====
# AUDIT_LOG_FILE = "mental_audit.json"
# audit_logs = []
#
# def log_decision(agent_name, action, reasoning, data=None):
#     """🧠 Audit logging"""
#     entry = {
#         "timestamp": datetime.now().isoformat(),
#         "agent": agent_name,
#         "action": action,
#         "reasoning": reasoning,
#         "data": data or {}
#     }
#     audit_logs.append(entry)
#     with open(AUDIT_LOG_FILE, "w") as f:
#         json.dump(audit_logs, f, indent=2)
#     print(f"📝 [AUDIT] {agent_name} → {action}")
#
# # ===== PRIVACY FILTER =====
# def redact_pii(text):
#     """🔐 Privacy Filter"""
#     if not text:
#         return text
#     text = re.sub(r'(PATIENT|USER)-\d+', r'\1-***', text)
#     text = re.sub(r'\+92\d{7}\d+', '+92*******', text)
#     text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)
#     text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '***@***.com', text)
#     return text
#
# # ===== LOCAL PATIENT RECORDS =====
# PATIENTS_FILE = "mental_patients.json"
#
# def load_patients():
#     if os.path.exists(PATIENTS_FILE):
#         with open(PATIENTS_FILE, "r") as f:
#             return json.load(f)
#     return {}
#
# def save_patients(patients):
#     with open(PATIENTS_FILE, "w") as f:
#         json.dump(patients, f, indent=2)
#
# def register_mental_case(patient_id, name, age, issue_type, email, phone, cnic=None):
#     """Register new mental health case locally"""
#     patients = load_patients()
#     patients[patient_id] = {
#         "name": name,
#         "age": age,
#         "issue_type": issue_type,
#         "email": email,
#         "phone": phone,
#         "cnic": cnic,
#         "registered_at": datetime.now().isoformat(),
#         "sessions": [],
#         "risk_level": "unknown"
#     }
#
#     save_patients(patients)
#
#     log_decision(
#         "MentalHealthAgent",
#         "case_registered_locally",
#         f"New case registered for issue type: {issue_type}",
#         {"patient_id": patient_id}
#     )
#
#     if email:
#         send_email_notification(
#             email,
#             "Mental Health Case Registered",
#             f"Salam {name}! Aapka mental health case register ho gaya hai. "
#             f"Our therapist will contact you soon."
#         )
#
#     return patients[patient_id]
#
# # # ===== MCP SERVER =====
# # mcp_server = MCPServerStdio(
# #     params={
# #         "command": "python",
# #         "args": ["agents_mcp.py"]
# #     },
# #     cache_tools_list=True,
# #     name="MentalMCP"
# # )
#
# # ===== MCP SERVERS (2 servers for inter-agent communication) =====
#
# # 1. Orchestrator MCP (for handoffs)
# orchestrator_mcp = MCPServerStdio(
#     params={
#         "command": "python",
#         "args": ["agent_orchestrator_mcp.py"]
#     },
#     cache_tools_list=True,
#     name="OrchestratorMCP"
# )
#
# # 2. Domain MCP (for actual work)
# domain_mcp = MCPServerStdio(
#     params={
#         "command": "python",
#         "args": ["agents_mcp.py"]
#     },
#     cache_tools_list=True,
#     name="DomainMCP"
# )
# #
# # # ===== MENTAL HEALTH AGENT =====
# # mental_agent = Agent(
# #     name="MentalHealthAgent",
# #     model=gemini_model,
# #     instructions=(
# #         "You are a compassionate digital mental health assistant serving patients in Pakistan.\n\n"
# #         "Your role is to analyze patient reports, detect emotional or psychological distress, "
# #         "and take appropriate actions through the available system tools. "
# #         "Decide actions logically — do not wait for explicit tool names from the user.\n\n"
# #         "🧠 Available capabilities (tools accessed via MCP):\n"
# #         "- Assess stress or anxiety levels based on reported symptoms and duration.\n"
# #         "- Assign a qualified therapist when a patient shows moderate or severe mental health concerns.\n"
# #         "- Schedule follow-up sessions to track recovery and provide continuity of care.\n"
# #         "- Trigger emergency mental health hotline if patient reports suicidal thoughts or immediate danger.\n\n"
# #         "🌐 Language: Respond naturally in Urdu or English, matching the patient’s input.\n"
# #         "🔐 Privacy: Never reveal CNIC, phone numbers, or full IDs — always redact sensitive data.\n"
# #         "📧 Notifications: When assigning therapists, scheduling follow-ups, or handling emergencies, "
# #         "ensure an email notification is sent to the registered patient.\n\n"
# #         "💡 Decision Flow:\n"
# #         "1. Evaluate the emotional condition and risk level.\n"
# #         "2. If low stress → reassure and suggest follow-up.\n"
# #         "3. If moderate or severe → assign therapist and plan follow-up.\n"
# #         "4. If suicidal or in crisis → immediately trigger hotline, then assign therapist and schedule follow-up.\n\n"
# #         "📋 Response Format:\n"
# #         "1) Reasoning: Explain why you took this action.\n"
# #         "2) Action Taken: Summarize what steps were performed.\n"
# #         "3) Next Steps: Suggest what should happen next for patient well-being."
# #     ),
# #     mcp_servers=[mcp_server]
# # )
# #
#
# # ===== MENTAL HEALTH AGENT =====
# mental_agent = Agent(
#     name="MentalHealthAgent",
#     model=gemini_model,
#     instructions=(
#         "You are a compassionate mental health assistant for Pakistan.\n\n"
#
#         "🤝 ORCHESTRATOR TOOLS (inter-agent communication):\n"
#         "- handoff_to_agent(from_agent='mental', to_agent, task_type, context, priority)\n"
#         "  → Crisis needing ambulance? → handoff to 'tracking' agent\n"
#         "  → Need medicine? → handoff to 'pharmacy' agent\n"
#         "- check_my_tasks(agent_name='mental')\n"
#         "  → Check for handoffs from maternal/other agents\n"
#         "- complete_task(handoff_id, result, completed_by='mental')\n"
#         "  → Complete received tasks\n"
#         "- query_agent_capabilities(agent_name)\n"
#         "  → Check agent capabilities\n\n"
#
#         "⚡ WORKFLOW:\n"
#         "1. Start: check_my_tasks('mental')\n"
#         "2. Suicidal emergency? → mental_emergency_hotline() + handoff_to_agent('mental', 'tracking', 'crisis_transport', {...}, 'urgent')\n"
#         "3. Need medication? → handoff_to_agent('mental', 'pharmacy', 'prescription_request', {...}, 'normal')\n\n"
#
#         "🧠 YOUR DOMAIN TOOLS:\n"
#         "- assess_stress_level(symptoms, duration_days)\n"
#         "- assign_therapist(patient_id, issue_type)\n"
#         "- schedule_followup(patient_id, days_from_now)\n"
#         "- mental_emergency_hotline(lat, lon, emergency_desc)\n\n"
#
#         "🌐 Language: Urdu or English\n"
#         "🔐 Privacy: Never reveal CNIC, phone numbers, full IDs\n"
#         "📧 Notifications: Send to patients\n\n"
#
#         "💡 Decision Flow:\n"
#         "1. Evaluate emotional condition\n"
#         "2. Low stress → reassure + follow-up\n"
#         "3. Moderate/severe → assign therapist + follow-up\n"
#         "4. Crisis → hotline + handoff to tracking\n\n"
#
#         "📋 Format: 1) Reasoning 2) Action 3) Next Steps"
#     ),
#     mcp_servers=[orchestrator_mcp, domain_mcp]
# )
#
# # ===== RETRY LOGIC =====
# async def run_with_retry(agent, query, max_retries=3):
#     """🔄 Retry with fallback"""
#     for attempt in range(max_retries):
#         try:
#             result = await Runner.run(agent, query)
#             return result
#         except Exception as e:
#             print(f"⚠️ Attempt {attempt + 1} failed: {e}")
#             if attempt == max_retries - 1:
#                 return {"final_output": "System offline. Hotline fallback activated."}
#             await asyncio.sleep(1)
#
# # ===== DEMO =====
# async def run_demo():
#     async with orchestrator_mcp, domain_mcp:
#     # async with mcp_server:
#         try:
#             await orchestrator_mcp.connect()
#             await domain_mcp.connect()
#             print("✅ Both MCP servers connected\n")
#             # await mcp_server.connect()
#             # print("✅ MCP Connected\n")
#         except Exception as e:
#             print(f"⚠️ MCP failed: {e}\n")
#
#         print("🧠 Mental Health Agent Started!\n")
#
#         # Test 1: Local registration
#         print("=" * 60)
#         print("TEST 1: Local Mental Case Registration")
#         patient_id = "PATIENT-001"
#         patient = register_mental_case(
#             patient_id=patient_id,
#             name="Ahmed Raza",
#             age=32,
#             issue_type="Depression",
#             email="hafizalaibafaisal@gmail.com",
#             phone="+923001234567",
#             cnic="35202-1234567-1"
#         )
#         print(f"✅ Local registration: {patient['name']}, Issue: {patient['issue_type']}\n")
#
#         # Test 2: Stress level assessment
#         print("=" * 60)
#         print("TEST 2: Stress Assessment via MCP")
#         query_stress = (
#             f"Patient {patient_id} reports sadness, low sleep, anxiety, "
#             f"and loss of interest for the past 14 days. Evaluate stress and determine risk level."
#         )
#
#         result_stress = await run_with_retry(mental_agent, query_stress)
#         output_stress = result_stress.final_output if hasattr(result_stress, "final_output") else str(result_stress)
#         print("✅ [OUTPUT]")
#         print(redact_pii(output_stress))
#         print()
#
#         log_decision(
#             "MentalHealthAgent",
#             "stress_assessed",
#             "Stress level evaluated based on reported symptoms",
#             {"patient_id": patient_id}
#         )
#
#         # Test 3: Assign therapist
#         print("=" * 60)
#         print("TEST 3: Assign Therapist via MCP")
#         query_therapist = (
#             f"Assign an appropriate therapist to patient {patient_id} who is experiencing depression."
#         )
#
#         result_therapist = await run_with_retry(mental_agent, query_therapist)
#         output_therapist = result_therapist.final_output if hasattr(result_therapist, "final_output") else str(
#             result_therapist)
#         print("✅ [OUTPUT]")
#         print(output_therapist)
#         print()
#
#         log_decision(
#             "MentalHealthAgent",
#             "therapist_assigned",
#             "Therapist assigned based on patient condition",
#             {"patient_id": patient_id}
#         )
#
#         # Test 4: Schedule follow-up session
#         print("=" * 60)
#         print("TEST 4: Follow-up Scheduling via MCP")
#         query_followup = (
#             f"Schedule a follow-up appointment for patient {patient_id} after 7 days to monitor progress."
#         )
#
#         result_followup = await run_with_retry(mental_agent, query_followup)
#         output_followup = result_followup.final_output if hasattr(result_followup, "final_output") else str(
#             result_followup)
#         print("✅ [OUTPUT]")
#         print(output_followup)
#         print()
#
#         log_decision(
#             "MentalHealthAgent",
#             "followup_scheduled",
#             "Follow-up session scheduled",
#             {"patient_id": patient_id}
#         )
#
#         # Test 5: Emergency hotline
#         print("=" * 60)
#         print("TEST 5: Mental Health Emergency Hotline via MCP")
#         query_hotline = (
#             f"Emergency reported at coordinates 31.50, 74.35. "
#             f"Patient {patient_id} is showing suicidal behavior. Trigger appropriate emergency response."
#         )
#
#         result_hotline = await run_with_retry(mental_agent, query_hotline)
#         output_hotline = result_hotline.final_output if hasattr(result_hotline, "final_output") else str(result_hotline)
#         print("✅ [OUTPUT]")
#         print(redact_pii(output_hotline))
#         print()
#
#         log_decision(
#             "MentalHealthAgent",
#             "hotline_alert_triggered",
#             "Emergency hotline triggered for high-risk case",
#             {"patient_id": patient_id}
#         )
#
#         print("=" * 60)
#         print(f"\n📊 Total audit logs: {len(audit_logs)}")
#         print(f"💾 Logs saved to: {AUDIT_LOG_FILE}")
#
#         await orchestrator_mcp.cleanup()
#         await domain_mcp.cleanup()
#
# if __name__ == "__main__":
#     asyncio.run(run_demo())


# mental_health_agent.py - COMPLETE FIXED VERSION
import asyncio
import json
import os
import re
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

# ===== LOAD ENV =====
from dotenv import load_dotenv
load_dotenv()

# ===== GEMINI SETUP =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# ===== EMAIL CONFIG =====
SENDER_EMAIL = "nooreasal786@gmail.com"
APP_PASSWORD = "irph tole tuqr vfmi"

def send_email_notification(receiver_email, subject, body):
    """📧 Email notification"""
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg.set_content(body)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        print(f"✉️ Email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ===== AUDIT LOGS =====
AUDIT_LOG_FILE = "mental_audit.json"
audit_logs = []

def log_decision(agent_name, action, reasoning, data=None):
    """🧠 Audit logging"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "reasoning": reasoning,
        "data": data or {}
    }
    audit_logs.append(entry)
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(audit_logs, f, indent=2)
    print(f"📝 [AUDIT] {agent_name} → {action}")

# ===== PRIVACY FILTER =====
def redact_pii(text):
    """🔐 Privacy Filter"""
    if not text:
        return text
    text = re.sub(r'(PATIENT|USER)-\d+', r'\1-***', text)
    text = re.sub(r'\+92\d{7}\d+', '+92*******', text)
    text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '***@***.com', text)
    return text

# ===== LOCAL PATIENT RECORDS =====
PATIENTS_FILE = "mental_patients.json"

def load_patients():
    if os.path.exists(PATIENTS_FILE):
        with open(PATIENTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_patients(patients):
    with open(PATIENTS_FILE, "w") as f:
        json.dump(patients, f, indent=2)

def register_mental_case(patient_id, name, age, issue_type, email, phone, cnic=None):
    """Register new mental health case locally"""
    patients = load_patients()
    patients[patient_id] = {
        "name": name,
        "age": age,
        "issue_type": issue_type,
        "email": email,
        "phone": phone,
        "cnic": cnic,
        "registered_at": datetime.now().isoformat(),
        "sessions": [],
        "risk_level": "unknown"
    }

    save_patients(patients)

    log_decision(
        "MentalHealthAgent",
        "case_registered_locally",
        f"New case registered for issue type: {issue_type}",
        {"patient_id": patient_id}
    )

    if email:
        send_email_notification(
            email,
            "Mental Health Case Registered",
            f"Salam {name}! Aapka mental health case register ho gaya hai. "
            f"Our therapist will contact you soon."
        )

    return patients[patient_id]

# ===== MCP SERVERS (2 servers) =====

# 1. Orchestrator MCP (for handoffs)
orchestrator_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": ["agent_orchestrator_mcp.py"]
    },
    cache_tools_list=True,
    name="OrchestratorMCP"
)

# 2. Domain MCP (for actual work)
domain_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": ["agents_mcp.py"]
    },
    cache_tools_list=True,
    name="DomainMCP"
)

# ===== MENTAL HEALTH AGENT WITH HANDOFF =====
mental_agent = Agent(
    name="MentalHealthAgent",
    model=gemini_model,
    instructions=(
        "You are a compassionate mental health assistant for Pakistan.\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🔄 INTER-AGENT HANDOFF SYSTEM\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "STEP 1: CHECK INCOMING TASKS\n"
        "→ ALWAYS call check_my_tasks('mental') at START\n"
        "→ Process pending handoffs from other agents FIRST\n\n"

        "STEP 2: DETECT IF YOU NEED ANOTHER AGENT\n\n"

        "→ TRACKING AGENT (Emergency Transport):\n"
        "  Keywords: ambulance, emergency transport, crisis location, suicidal with location\n"
        "  Example: 'Suicidal patient at location 31.52, 74.35' → handoff_to_agent(to_agent='tracking')\n\n"

        "→ PHARMACY AGENT (Medication):\n"
        "  Keywords: antidepressants, medication, prescription, medicine, psychiatric drugs\n"
        "  Example: 'Patient needs antidepressants' → handoff_to_agent(to_agent='pharmacy')\n\n"

        "→ MATERNAL AGENT (Postpartum Depression):\n"
        "  Keywords: postpartum depression, after delivery, new mother depression\n"
        "  Example: 'New mother with depression' → handoff_to_agent(to_agent='maternal')\n\n"

        "STEP 3: EXECUTE HANDOFF\n"
        "handoff_to_agent(\n"
        "    from_agent='mental',\n"
        "    to_agent='<target>',\n"
        "    task_type='<specific_task>',\n"
        "    context={'patient_details': '...', 'location': {...}, 'priority': 'urgent'},\n"
        "    priority='urgent'  # if crisis\n"
        ")\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🧠 YOUR DOMAIN TOOLS\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "- assess_stress_level(symptoms, duration_days)\n"
        "  → Evaluate anxiety, depression, stress levels\n"
        "  → Returns risk score (low/moderate/high/critical)\n\n"

        "- assign_therapist(patient_id, issue_type)\n"
        "  → Match patient with appropriate therapist\n"
        "  → Returns therapist name, specialty, session_id\n\n"

        "- schedule_followup(patient_id, days_from_now)\n"
        "  → Book follow-up therapy session\n"
        "  → Default: 7 days for moderate cases, 3 days for high risk\n\n"

        "- mental_emergency_hotline(lat, lon, emergency_desc)\n"
        "  → Activate crisis response (1166 hotline)\n"
        "  → ALWAYS call this for suicidal thoughts\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🧠 DECISION LOGIC\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "SCENARIO 1: Suicidal Crisis with Location\n"
        "User: 'I want to end my life, I'm at location 31.52, 74.35'\n"
        "You:\n"
        "  1. mental_emergency_hotline(31.52, 74.35, 'suicidal thoughts')\n"
        "  2. handoff_to_agent(to_agent='tracking', task_type='crisis_transport', priority='urgent')\n"
        "  3. assign_therapist(patient_id, 'crisis')\n"
        "  4. Tell user: Help is on the way, you're not alone\n\n"

        "SCENARIO 2: Severe Anxiety/Depression\n"
        "User: 'I've been severely depressed for 2 months, can't function'\n"
        "You:\n"
        "  1. assess_stress_level('severe depression', 60)\n"
        "  2. assign_therapist(patient_id, 'depression')\n"
        "  3. schedule_followup(patient_id, 3)  # 3 days for high risk\n"
        "  4. Consider medication: handoff_to_agent(to_agent='pharmacy')\n\n"

        "SCENARIO 3: Postpartum Depression\n"
        "User: 'New mother feeling hopeless after delivery'\n"
        "You:\n"
        "  1. assess_stress_level('postpartum depression', 7)\n"
        "  2. handoff_to_agent(to_agent='maternal', task_type='postpartum_mental_health')\n"
        "  3. assign_therapist(patient_id, 'postpartum')\n\n"

        "SCENARIO 4: Medication Request\n"
        "User: 'I need antidepressants refill'\n"
        "You: handoff_to_agent(to_agent='pharmacy', task_type='psychiatric_medication')\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "📋 RESPONSE FORMAT\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "1️⃣ REASONING:\n"
        "   'Detected [symptoms/risk level]. This requires [immediate/urgent/routine] action.'\n\n"

        "2️⃣ ACTION TAKEN:\n"
        "   '- Called assess_stress_level() → High risk detected'\n"
        "   '- Called assign_therapist() → Dr. Ahmed assigned'\n"
        "   '- Called handoff_to_agent() → Tracking agent for emergency transport'\n\n"

        "3️⃣ RESULT:\n"
        "   'Crisis counselor assigned. Ambulance en route. You're safe.'\n\n"

        "4️⃣ NEXT STEPS:\n"
        "   'Crisis hotline: 1166. Therapist will contact you in 30 minutes.'\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🔐 CRITICAL RULES\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "✅ DO:\n"
        "- ALWAYS call check_my_tasks() first\n"
        "- Use handoff_to_agent() when triggers detected\n"
        "- Prioritize patient safety above all\n"
        "- Respond in patient's language (Urdu/English)\n"
        "- Show empathy and validate feelings\n\n"

        "❌ DON'T:\n"
        "- Skip crisis interventions\n"
        "- Handle ambulance dispatch yourself (handoff to tracking)\n"
        "- Provide medication directly (handoff to pharmacy)\n"
        "- Share patient personal info\n\n"

        "🌐 MULTILINGUAL: Match user's language\n"
        "📱 DEGRADED MODE: If tools fail → Provide hotline (1166)\n"
        "🔐 PRIVACY: Redact CNIC, phone, full patient IDs\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "Remember: You save lives. Be compassionate, be fast, be thorough. 💜"
    ),
    mcp_servers=[orchestrator_mcp, domain_mcp]
)

# ===== RETRY LOGIC =====
async def run_with_retry(agent, query, max_retries=3):
    """🔄 Retry with fallback"""
    for attempt in range(max_retries):
        try:
            result = await Runner.run(agent, query)
            return result
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return {"final_output": "System offline. Hotline fallback activated: Call 1166"}
            await asyncio.sleep(1)

# ===== DEMO (FOR TESTING ONLY) =====
async def run_demo():
    async with orchestrator_mcp, domain_mcp:
        try:
            await orchestrator_mcp.connect()
            await domain_mcp.connect()
            print("✅ Both MCP servers connected\n")
        except Exception as e:
            print(f"⚠️ MCP failed: {e}\n")

        print("🧠 Mental Health Agent Started!\n")

        # Test: Suicidal crisis with handoff
        print("=" * 60)
        print("TEST: Suicidal Crisis with Location")
        query = (
            "I'm feeling suicidal and want to end my life. "
            "I'm at location 31.5204, 74.3587. Please help."
        )

        result = await run_with_retry(mental_agent, query)
        output = result.final_output if hasattr(result, "final_output") else str(result)
        print("✅ [OUTPUT]")
        print(redact_pii(output))
        print()

        await orchestrator_mcp.cleanup()
        await domain_mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(run_demo())