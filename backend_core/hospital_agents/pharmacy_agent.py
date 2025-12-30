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

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

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
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

if not SENDER_EMAIL or not APP_PASSWORD:
    print("⚠️ Email credentials not found in .env, email features will be disabled.")


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
        "args": [os.path.join(BASE_DIR, "mcp_servers/orchestrator_mcp/agent_orchestrator_mcp.py")]
    },
    cache_tools_list=True,
    name="OrchestratorMCP"
)

# 2. Domain MCP (for actual work)
domain_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": [os.path.join(BASE_DIR, "mcp_servers/core_agents_mcp/agents_mcp.py")]
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
        "→ Process prescription requests from mental/maternal hospital_agents FIRST\n\n"

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