# # pharmacy_agent.py - Complete Pharmacy Agent
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
# import random
#
# # ===== LOAD ENV =====
# from dotenv import load_dotenv
# load_dotenv()
#
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
#
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
# AUDIT_LOG_FILE = "pharmacy_audit.json"
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
#     text = re.sub(r'(PATIENT|PRESCRIPTION|RX)-\d+', r'\1-***', text)
#     text = re.sub(r'\+92\d{7}\d+', '+92*******', text)
#     text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)
#     text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '***@***.com', text)
#     return text
#
# # ===== LOCAL PHARMACY DATABASE =====
# PHARMACY_FILE = "pharmacy_stock.json"
# PRESCRIPTIONS_FILE = "pharmacy_prescriptions.json"
#
# def load_pharmacy_stock():
#     if os.path.exists(PHARMACY_FILE):
#         with open(PHARMACY_FILE, "r") as f:
#             return json.load(f)
#     # Default stock
#     return {
#         "site_LHR_001": {
#             "name": "Services Hospital Pharmacy",
#             "stock": {
#                 "paracetamol": {"count": 500, "unit": "tablets"},
#                 "amoxicillin": {"count": 120, "unit": "capsules"},
#                 "iron_supplement": {"count": 200, "unit": "tablets"},
#                 "folic_acid": {"count": 150, "unit": "tablets"},
#                 "oxytocin": {"count": 30, "unit": "vials"}
#             }
#         },
#         "site_LHR_002": {
#             "name": "Mayo Hospital Pharmacy",
#             "stock": {
#                 "paracetamol": {"count": 300, "unit": "tablets"},
#                 "amoxicillin": {"count": 5, "unit": "capsules"},
#                 "iron_supplement": {"count": 50, "unit": "tablets"},
#                 "folic_acid": {"count": 80, "unit": "tablets"},
#                 "oxytocin": {"count": 10, "unit": "vials"}
#             }
#         }
#     }
#
# def save_pharmacy_stock(stock):
#     with open(PHARMACY_FILE, "w") as f:
#         json.dump(stock, f, indent=2)
#
# def load_prescriptions():
#     if os.path.exists(PRESCRIPTIONS_FILE):
#         with open(PRESCRIPTIONS_FILE, "r") as f:
#             return json.load(f)
#     return []
#
# def save_prescriptions(prescriptions):
#     with open(PRESCRIPTIONS_FILE, "w") as f:
#         json.dump(prescriptions, f, indent=2)
#
# # ===== LOCAL PHARMACY FUNCTIONS =====
#
# def check_local_stock(site_id, medicine):
#     """Check stock locally"""
#     stock = load_pharmacy_stock()
#     if site_id in stock and medicine in stock[site_id]["stock"]:
#         return stock[site_id]["stock"][medicine]["count"]
#     return 0
#
# def predict_local_shortage(medicine):
#     """Predict shortage across all sites"""
#     stock = load_pharmacy_stock()
#     total = 0
#
#     for site_id, site in stock.items():
#         if medicine in site["stock"]:
#             total += site["stock"][medicine]["count"]
#
#     # Simple prediction
#     if total < 50:
#         risk = "critical"
#         days_remaining = 3
#     elif total < 150:
#         risk = "warning"
#         days_remaining = 10
#     else:
#         risk = "ok"
#         days_remaining = 30
#
#     log_decision(
#         "PharmacyAgent",
#         "shortage_predicted",
#         f"Shortage prediction for {medicine}: {risk}",
#         {"medicine": medicine, "total_stock": total, "risk": risk}
#     )
#
#     return {
#         "medicine": medicine,
#         "total_stock": total,
#         "risk": risk,
#         "days_remaining": days_remaining
#     }
#
# def create_purchase_order(medicine, quantity, site_id):
#     """Generate auto purchase order"""
#     po_id = f"PO-{random.randint(10000, 99999)}"
#
#     order = {
#         "po_id": po_id,
#         "medicine": medicine,
#         "quantity": quantity,
#         "site_id": site_id,
#         "status": "pending",
#         "created_at": datetime.now().isoformat()
#     }
#
#     log_decision(
#         "PharmacyAgent",
#         "purchase_order_created",
#         f"Auto PO generated for {medicine}",
#         {"po_id": po_id, "medicine": medicine, "quantity": quantity}
#     )
#
#     return order
#
# def reallocate_stock(from_site, to_site, medicine, quantity):
#     """Reallocate medicine between facilities"""
#     stock = load_pharmacy_stock()
#
#     if from_site not in stock or to_site not in stock:
#         return {"status": "failed", "message": "Invalid site IDs"}
#
#     if medicine not in stock[from_site]["stock"]:
#         return {"status": "failed", "message": "Medicine not available at source"}
#
#     available = stock[from_site]["stock"][medicine]["count"]
#
#     if available < quantity:
#         return {"status": "failed", "message": "Insufficient stock at source"}
#
#     # Transfer
#     stock[from_site]["stock"][medicine]["count"] -= quantity
#
#     if medicine not in stock[to_site]["stock"]:
#         stock[to_site]["stock"][medicine] = {"count": 0, "unit": stock[from_site]["stock"][medicine]["unit"]}
#
#     stock[to_site]["stock"][medicine]["count"] += quantity
#
#     save_pharmacy_stock(stock)
#
#     log_decision(
#         "PharmacyAgent",
#         "stock_reallocated",
#         f"Transferred {quantity} units of {medicine} from {from_site} to {to_site}",
#         {"from": from_site, "to": to_site, "medicine": medicine, "quantity": quantity}
#     )
#
#     return {
#         "status": "success",
#         "from_site": from_site,
#         "to_site": to_site,
#         "medicine": medicine,
#         "quantity": quantity
#     }
#
# def create_prescription(patient_id, medicine, dosage, duration_days, email=None):
#     """Create and log prescription"""
#     prescriptions = load_prescriptions()
#
#     rx_id = f"RX-{random.randint(10000, 99999)}"
#
#     prescription = {
#         "rx_id": rx_id,
#         "patient_id": patient_id,
#         "medicine": medicine,
#         "dosage": dosage,
#         "duration_days": duration_days,
#         "created_at": datetime.now().isoformat(),
#         "status": "active"
#     }
#
#     prescriptions.append(prescription)
#     save_prescriptions(prescriptions)
#
#     log_decision(
#         "PharmacyAgent",
#         "prescription_created",
#         f"Prescription {rx_id} for {medicine}",
#         {"rx_id": rx_id, "patient_id": patient_id}
#     )
#
#     # Send email
#     if email:
#         send_email_notification(
#             email,
#             "💊 Prescription Ready",
#             f"Aapka prescription tayar hai:\n\n"
#             f"🆔 Prescription ID: {rx_id}\n"
#             f"💊 Dawai: {medicine}\n"
#             f"📋 Dosage: {dosage}\n"
#             f"⏱️ Duration: {duration_days} days\n\n"
#             f"Nazdiki pharmacy se le sakte hain."
#         )
#
#     return prescription
#
# # # ===== MCP SERVER =====
# # mcp_server = MCPServerStdio(
# #     params={
# #         "command": "python",
# #         "args": ["agents_mcp.py"]
# #     },
# #     cache_tools_list=True,
# #     name="PharmacyMCP"
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
# # # ===== PHARMACY AGENT =====
# # pharmacy_agent = Agent(
# #     name="PharmacyAgent",
# #     model=gemini_model,
# #     instructions=(
# #         "You are a pharmacy management agent for Pakistan's healthcare system.\n\n"
# #         "Your role is to monitor medicine stock, predict shortages, generate purchase orders, "
# #         "reallocate stock between facilities, and manage prescriptions.\n\n"
# #         "🧠 Available capabilities (tools via MCP):\n"
# #         "- Check stock levels at specific facilities\n"
# #         "- Predict medicine shortages across all sites\n"
# #         "- Generate automatic purchase orders when stock is low\n"
# #         "- Reallocate medicines from surplus to deficit facilities\n"
# #         "- Create and manage patient prescriptions\n"
# #         "- Detect abnormal consumption patterns (abuse detection)\n"
# #         "- Send dosage alerts via email/SMS\n\n"
# #         "🌐 Language: Respond in Urdu or English based on user input.\n"
# #         "🔐 Privacy: Never reveal full patient IDs or prescription numbers.\n"
# #         "📧 Notifications: Send email alerts for low stock, prescription ready, and dosage reminders.\n\n"
# #         "💡 Decision Flow:\n"
# #         "1. Monitor stock levels → if low, predict shortage\n"
# #         "2. If critical shortage → generate purchase order\n"
# #         "3. If one site has surplus and another deficit → reallocate stock\n"
# #         "4. For prescriptions → create RX, notify patient, track consumption\n"
# #         "5. If abnormal consumption detected → flag for review\n\n"
# #         "📋 Response Format:\n"
# #         "1) Reasoning: Why this action was taken\n"
# #         "2) Action: What was done\n"
# #         "3) Next Steps: Recommendations"
# #     ),
# #     mcp_servers=[mcp_server]
# # )
#
# # ===== PHARMACY AGENT =====
# pharmacy_agent = Agent(
#     name="PharmacyAgent",
#     model=gemini_model,
#     instructions=(
#         "You are a pharmacy management agent for Pakistan.\n\n"
#
#         "🤝 ORCHESTRATOR TOOLS (inter-agent communication):\n"
#         "- handoff_to_agent(from_agent='pharmacy', to_agent, task_type, context, priority)\n"
#         "  → Emergency drug transport? → handoff to 'tracking' agent\n"
#         "  → Pharmaceutical waste? → handoff to 'waste' agent\n"
#         "- check_my_tasks(agent_name='pharmacy')\n"
#         "  → Check for prescription requests from mental/maternal agents\n"
#         "- complete_task(handoff_id, result, completed_by='pharmacy')\n"
#         "  → Complete prescription requests\n"
#         "- query_agent_capabilities(agent_name)\n"
#         "  → Check capabilities\n\n"
#
#         "⚡ WORKFLOW:\n"
#         "1. Start: check_my_tasks('pharmacy')\n"
#         "2. Critical shortage? → generate_purchase_order() or reallocate_medicine()\n"
#         "3. Pharmaceutical waste? → handoff_to_agent('pharmacy', 'waste', 'pharmaceutical_disposal', {...}, 'normal')\n\n"
#
#         "💊 YOUR DOMAIN TOOLS:\n"
#         "- check_pharmacy_stock(site_id, medicine)\n"
#         "- predict_medicine_shortage(medicine)\n"
#         "- generate_purchase_order(medicine, quantity, site_id)\n"
#         "- reallocate_medicine(from_site, to_site, medicine, quantity)\n"
#         "- create_patient_prescription(patient_id, medicine, dosage, duration_days)\n"
#         "- detect_abnormal_consumption(medicine, patient_id, daily_usage)\n\n"
#
#         "🌐 Language: Urdu or English\n"
#         "🔐 Privacy: Never reveal full patient IDs\n"
#         "📧 Notifications: Email alerts for low stock\n\n"
#
#         "💡 Decision Flow:\n"
#         "1. Monitor stock → if low, predict shortage\n"
#         "2. Critical shortage → purchase order\n"
#         "3. Surplus at one site + deficit at another → reallocate\n"
#         "4. Create RX → notify patient\n"
#         "5. Abnormal consumption → flag\n\n"
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
#                 return {"final_output": "System offline. SMS fallback activated."}
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
#         print("💊 Pharmacy Agent Started!\n")
#
#         # Test 1: Check stock
#         print("=" * 60)
#         print("TEST 1: Check Stock Levels via MCP")
#         query_stock = (
#             "Check stock of iron_supplement at site_LHR_001. "
#             "If low, also check site_LHR_002."
#         )
#
#         result_stock = await run_with_retry(pharmacy_agent, query_stock)
#         output_stock = result_stock.final_output if hasattr(result_stock, "final_output") else str(result_stock)
#         print("✅ [OUTPUT]")
#         print(output_stock)
#         print()
#
#         # Test 2: Predict shortage
#         print("=" * 60)
#         print("TEST 2: Predict Shortage for Amoxicillin")
#         shortage = predict_local_shortage("amoxicillin")
#         print(f"✅ Shortage Analysis: {shortage}")
#         print()
#
#         # Test 3: Generate purchase order
#         print("=" * 60)
#         print("TEST 3: Auto Purchase Order via MCP")
#         query_po = (
#             "Stock of amoxicillin is critically low (total: 125 units). "
#             "Generate purchase order for 500 units at site_LHR_002."
#         )
#
#         result_po = await run_with_retry(pharmacy_agent, query_po)
#         output_po = result_po.final_output if hasattr(result_po, "final_output") else str(result_po)
#         print("✅ [OUTPUT]")
#         print(output_po)
#         print()
#
#         # Test 4: Stock reallocation
#         print("=" * 60)
#         print("TEST 4: Reallocate Stock Between Sites")
#         realloc = reallocate_stock("site_LHR_001", "site_LHR_002", "paracetamol", 100)
#         print(f"✅ Reallocation: {realloc}")
#         print()
#
#         # Test 5: Create prescription
#         print("=" * 60)
#         print("TEST 5: Create Prescription for Patient")
#         prescription = create_prescription(
#             patient_id="PATIENT-001",
#             medicine="iron_supplement",
#             dosage="1 tablet daily after meals",
#             duration_days=30,
#             email="hafizalaibafaisal@gmail.com"
#         )
#         print(f"✅ Prescription: {redact_pii(json.dumps(prescription, indent=2))}")
#         print()
#
#         # Test 6: Natural query with LLM decision
#         print("=" * 60)
#         print("TEST 6: Natural Query - LLM Decides Actions")
#         query_natural = (
#             "Iron supplements ki stock bohot kam hai site_LHR_002 mein. "
#             "Kya site_LHR_001 se transfer kar sakte hain? Ya purchase order banana hoga?"
#         )
#
#         result_natural = await run_with_retry(pharmacy_agent, query_natural)
#         output_natural = result_natural.final_output if hasattr(result_natural, "final_output") else str(result_natural)
#         print("✅ [OUTPUT]")
#         print(redact_pii(output_natural))
#         print()
#
#         print("=" * 60)
#         print(f"\n📊 Total audit logs: {len(audit_logs)}")
#         print(f"💾 Logs saved to: {AUDIT_LOG_FILE}")
#         print(f"📦 Stock data: {PHARMACY_FILE}")
#         print(f"📋 Prescriptions: {PRESCRIPTIONS_FILE}")
#
#         await orchestrator_mcp.cleanup()
#         await domain_mcp.cleanup()
#
# if __name__ == "__main__":
#     asyncio.run(run_demo())


# pharmacy_agent.py - COMPLETE FIXED VERSION WITH HANDOFF
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
import random

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
AUDIT_LOG_FILE = "pharmacy_audit.json"
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
    text = re.sub(r'(PATIENT|PRESCRIPTION|RX)-\d+', r'\1-***', text)
    text = re.sub(r'\+92\d{7}\d+', '+92*******', text)
    text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '***@***.com', text)
    return text

# ===== LOCAL PHARMACY DATABASE =====
PHARMACY_FILE = "pharmacy_stock.json"
PRESCRIPTIONS_FILE = "pharmacy_prescriptions.json"

def load_pharmacy_stock():
    if os.path.exists(PHARMACY_FILE):
        with open(PHARMACY_FILE, "r") as f:
            return json.load(f)
    return {
        "site_LHR_001": {
            "name": "Services Hospital Pharmacy",
            "stock": {
                "paracetamol": {"count": 500, "unit": "tablets"},
                "amoxicillin": {"count": 120, "unit": "capsules"},
                "iron_supplement": {"count": 200, "unit": "tablets"},
                "folic_acid": {"count": 150, "unit": "tablets"},
                "oxytocin": {"count": 30, "unit": "vials"}
            }
        },
        "site_LHR_002": {
            "name": "Mayo Hospital Pharmacy",
            "stock": {
                "paracetamol": {"count": 300, "unit": "tablets"},
                "amoxicillin": {"count": 5, "unit": "capsules"},
                "iron_supplement": {"count": 50, "unit": "tablets"},
                "folic_acid": {"count": 80, "unit": "tablets"},
                "oxytocin": {"count": 10, "unit": "vials"}
            }
        }
    }

def save_pharmacy_stock(stock):
    with open(PHARMACY_FILE, "w") as f:
        json.dump(stock, f, indent=2)

def load_prescriptions():
    if os.path.exists(PRESCRIPTIONS_FILE):
        with open(PRESCRIPTIONS_FILE, "r") as f:
            return json.load(f)
    return []

def save_prescriptions(prescriptions):
    with open(PRESCRIPTIONS_FILE, "w") as f:
        json.dump(prescriptions, f, indent=2)

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

# ===== PHARMACY AGENT WITH HANDOFF =====
pharmacy_agent = Agent(
    name="PharmacyAgent",
    model=gemini_model,
    instructions=(
        "You are a pharmacy management agent for Pakistan's healthcare system.\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🔄 INTER-AGENT HANDOFF SYSTEM\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "STEP 1: CHECK INCOMING TASKS\n"
        "→ ALWAYS call check_my_tasks('pharmacy') at START\n"
        "→ Process prescription requests from mental/maternal agents FIRST\n\n"

        "STEP 2: DETECT IF YOU NEED ANOTHER AGENT\n\n"

        "→ WASTE AGENT (Pharmaceutical Waste):\n"
        "  Keywords: expired medicine, pharmaceutical waste, disposal, hazardous waste\n"
        "  Example: 'Expired medicines need disposal' → handoff_to_agent(to_agent='waste')\n\n"

        "→ TRACKING AGENT (Emergency Medicine Transport):\n"
        "  Keywords: emergency medicine delivery, urgent transport, ambulance with medicine\n"
        "  Example: 'Need urgent medicine transport' → handoff_to_agent(to_agent='tracking')\n\n"

        "→ MATERNAL AGENT (Pregnancy-related Medicines):\n"
        "  Keywords: prenatal vitamins, iron supplements for pregnant, folic acid pregnancy\n"
        "  Example: 'Pregnant woman needs iron' → handoff_to_agent(to_agent='maternal')\n\n"

        "STEP 3: EXECUTE HANDOFF\n"
        "handoff_to_agent(\n"
        "    from_agent='pharmacy',\n"
        "    to_agent='<target>',\n"
        "    task_type='<specific_task>',\n"
        "    context={'medicine': '...', 'quantity': ..., 'urgency': 'high'},\n"
        "    priority='urgent'  # if emergency\n"
        ")\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "💊 YOUR DOMAIN TOOLS\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "- check_pharmacy_stock(site_id, medicine)\n"
        "  → Check stock at specific facility\n"
        "  → Returns count, risk level (ok/low/critical)\n\n"

        "- predict_medicine_shortage(medicine)\n"
        "  → Predict shortage across all sites\n"
        "  → Returns total stock, risk level, days remaining\n\n"

        "- generate_purchase_order(medicine, quantity, site_id)\n"
        "  → Auto-generate PO for restocking\n"
        "  → Returns PO ID, estimated delivery\n\n"

        "- reallocate_medicine(from_site, to_site, medicine, quantity)\n"
        "  → Transfer stock between facilities\n"
        "  → Returns transfer confirmation\n\n"

        "- create_patient_prescription(patient_id, medicine, dosage, duration_days)\n"
        "  → Generate prescription for patient\n"
        "  → Returns RX ID, sends email notification\n\n"

        "- detect_abnormal_consumption(medicine, patient_id, daily_usage)\n"
        "  → Flag potential medicine abuse\n"
        "  → Returns risk flag (normal/suspicious/high_risk_abuse)\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🧠 DECISION LOGIC\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "SCENARIO 1: Stock Check\n"
        "User: 'Check iron supplement stock at site_LHR_001'\n"
        "You:\n"
        "  1. check_pharmacy_stock('site_LHR_001', 'iron_supplement')\n"
        "  2. Return: Stock level, risk status\n"
        "  3. If low: Suggest reallocation or purchase order\n\n"

        "SCENARIO 2: Critical Shortage\n"
        "User: 'Amoxicillin is running out across all sites'\n"
        "You:\n"
        "  1. predict_medicine_shortage('amoxicillin')\n"
        "  2. generate_purchase_order('amoxicillin', 500, 'site_LHR_002')\n"
        "  3. Send alert email to procurement team\n\n"

        "SCENARIO 3: Stock Reallocation\n"
        "User: 'Site LHR_002 needs paracetamol but LHR_001 has surplus'\n"
        "You:\n"
        "  1. check_pharmacy_stock() for both sites\n"
        "  2. reallocate_medicine('site_LHR_001', 'site_LHR_002', 'paracetamol', 100)\n"
        "  3. Update audit logs\n\n"

        "SCENARIO 4: Prescription Request (from Mental/Maternal Agent)\n"
        "User: 'Create prescription for antidepressants for patient MAT-001'\n"
        "You:\n"
        "  1. check_my_tasks('pharmacy') → Find handoff from mental agent\n"
        "  2. create_patient_prescription('MAT-001', 'antidepressant', '1 daily', 30)\n"
        "  3. complete_task(handoff_id, result)\n"
        "  4. Send email with prescription details\n\n"

        "SCENARIO 5: Pharmaceutical Waste\n"
        "User: 'We have 50 units of expired antibiotics to dispose'\n"
        "You: handoff_to_agent(to_agent='waste', task_type='pharmaceutical_disposal')\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "📋 RESPONSE FORMAT\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "1️⃣ REASONING:\n"
        "   'Detected [low stock/shortage/request]. This requires [action].'\n\n"

        "2️⃣ ACTION TAKEN:\n"
        "   '- Called check_pharmacy_stock() → 200 units available'\n"
        "   '- Called generate_purchase_order() → PO-12345 created'\n\n"

        "3️⃣ RESULT:\n"
        "   'Stock sufficient for 30 days. Monitoring daily consumption.'\n\n"

        "4️⃣ NEXT STEPS:\n"
        "   'Set alert for when stock drops below 100 units.'\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🔐 CRITICAL RULES\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "✅ DO:\n"
        "- ALWAYS call check_my_tasks() first\n"
        "- Use handoff_to_agent() when triggers detected\n"
        "- Monitor stock levels proactively\n"
        "- Respond in user's language (Urdu/English)\n"
        "- Redact patient IDs in responses\n\n"

        "❌ DON'T:\n"
        "- Handle waste disposal yourself (handoff to waste agent)\n"
        "- Ignore low stock alerts\n"
        "- Share full patient/prescription IDs\n\n"

        "🌐 MULTILINGUAL: Match user's language\n"
        "📱 DEGRADED MODE: If tools fail → provide manual contact numbers\n"
        "🔐 PRIVACY: Redact all sensitive IDs\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "Remember: Medicine availability saves lives. Be proactive! 💊"
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
                return {"final_output": "System offline. Contact pharmacy directly: 042-9920-1409"}
            await asyncio.sleep(1)

# ===== DEMO =====
async def run_demo():
    async with orchestrator_mcp, domain_mcp:
        try:
            await orchestrator_mcp.connect()
            await domain_mcp.connect()
            print("✅ Both MCP servers connected\n")
        except Exception as e:
            print(f"⚠️ MCP failed: {e}\n")

        print("💊 Pharmacy Agent Started!\n")

        # Test: Stock check with handoff if needed
        print("=" * 60)
        print("TEST: Stock Check with Potential Handoff")
        query = (
            "Check iron supplement stock at site_LHR_001. "
            "If low and needed for pregnant patient, coordinate with maternal agent."
        )

        result = await run_with_retry(pharmacy_agent, query)
        output = result.final_output if hasattr(result, "final_output") else str(result)
        print("✅ [OUTPUT]")
        print(redact_pii(output))
        print()

        await orchestrator_mcp.cleanup()
        await domain_mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(run_demo())