# criminal_agent.py - Complete Criminal Case Agent with 6-Month Follow-ups
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
AUDIT_LOG_FILE = "criminal_audit.json"
audit_logs = []


def log_decision(agent_name, action, reasoning, data=None, consent_token=None):
    """🧠 Audit logging with consent"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "reasoning": reasoning,
        "data": data or {},
        "consent_token": consent_token or "N/A"
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

    text = re.sub(r'(CASE|VICTIM|SUSPECT)-\d+', r'\1-***', text)
    text = re.sub(r'(PATIENT|VICTIM)-\d+', r'\1-***', text)
    text = re.sub(r'\+92\d{7}\d+', '+92*******', text)
    text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '***@***.com', text)
    text = re.sub(r'House #\d+', 'House #***', text)

    return text


# ===== MCP SERVERS =====
orchestrator_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": [os.path.join(BASE_DIR, "mcp_servers/orchestrator_mcp/agent_orchestrator_mcp.py")]
    },
    cache_tools_list=True,
    name="OrchestratorMCP"
)

domain_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": [os.path.join(BASE_DIR, "mcp_servers/core_agents_mcp/agents_mcp.py")]
    },
    cache_tools_list=True,
    name="DomainMCP"
)

# ===== CRIMINAL CASE AGENT =====
criminal_agent = Agent(
    name="CriminalCaseAgent",
    model=gemini_model,
    instructions=(
        "You are a criminal case detection agent for Pakistan with 6-month follow-up tracking.\n\n"

        "🤝 ORCHESTRATOR TOOLS (inter-agent communication):\n"
        "- handoff_to_agent(from_agent='criminal', to_agent, task_type, context, priority)\n"
        "  → Victim needs ambulance? → handoff to 'tracking' agent\n"
        "  → Victim needs mental support? → handoff to 'mental' agent\n"
        "- check_my_tasks(agent_name='criminal')\n"
        "- complete_task(handoff_id, result, completed_by='criminal')\n"
        "- query_agent_capabilities(agent_name)\n\n"

        "⚡ CORE WORKFLOW:\n"
        "1. Start: check_my_tasks('criminal')\n"
        "2. Classify injury → if suspicious, create case\n"
        "3. Critical case? → report_to_police()\n"
        "4. Schedule 6-month follow-up automatically\n"
        "5. Victim trauma? → handoff_to_agent('criminal', 'mental', 'trauma_support', {...}, 'high')\n\n"

        "⚖️ YOUR DOMAIN TOOLS:\n"
        "- classify_injury_local(injury_notes, injury_type)\n"
        "- create_case_report(patient_id, injury_notes, injury_type, location, cnic, victim_name)\n"
        "- report_to_police(case_id, case_data)\n"
        "- verify_identity_nadra(cnic)\n"
        "- collect_medical_evidence(case_id, evidence_type, evidence_notes)\n"
        "- transfer_evidence_to_forensics(evidence_id, case_id)\n"
        "- get_police_jurisdiction(location)\n"
        "- pseudonymize_case_data(case_data)\n\n"

        "📅 6-MONTH FOLLOW-UP TOOLS:\n"
        "- schedule_followup(case_id, followup_date=None, followup_type='case_status_check')\n"
        "  → Automatically called when creating case\n"
        "- check_pending_followups()\n"
        "  → Check if any cases need follow-up\n"
        "- check_case_closure_status(case_id)\n"
        "  → Is case still open after 6 months?\n"
        "- update_case_status(case_id, new_status, closure_notes=None)\n"
        "  → Mark case as closed/reopened\n"
        "- generate_followup_report(case_id)\n"
        "  → Full report with evidence + duration\n"
        "- send_followup_reminder(case_id, recipient_email)\n"
        "  → Send reminder to police/hospital\n\n"

        "🔐 CRITICAL PRIVACY:\n"
        "- ALWAYS pseudonymize before police reports\n"
        "- NEVER share victim names, CNIC externally\n"
        "- Maintain chain of custody\n"
        "- Log with consent tokens\n\n"

        "⚖️ AUTO-REPORT TRIGGERS:\n"
        "- Sexual violence (immediate)\n"
        "- Multiple assault injuries (immediate)\n"
        "- Gunshot/stab wounds (immediate)\n"
        "- Burn injuries (suspicious)\n"
        "- Domestic violence (immediate)\n\n"

        "📋 FOLLOW-UP LOGIC:\n"
        "1. When case created → auto-schedule 6-month follow-up\n"
        "2. After 6 months → check_case_closure_status()\n"
        "3. If still open → send_followup_reminder() to police\n"
        "4. If closed → generate_followup_report() for records\n\n"

        "🌐 Language: Urdu or English\n\n"

        "📋 Response Format:\n"
        "1) Reasoning: Why flagged\n"
        "2) Action: What done\n"
        "3) Privacy: How protected\n"
        "4) Follow-up: When scheduled\n"
        "5) Next Steps: Recommendations"
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
                return {"final_output": "System offline. Manual police reporting required."}
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

        print("⚖️ Criminal Case Agent with 6-Month Follow-ups!\n")
        print("=" * 70)

        # Test 1: Create case with auto follow-up
        print("=" * 70)
        print("TEST 1: Create Case + Schedule 6-Month Follow-up")
        print("-" * 70)

        query1 = (
            "Emergency room mein ek patient aya hai - PATIENT-001. "
            "Patient ki medical report: Multiple blunt trauma injuries. "
            "Patient reports being beaten by husband. "
            "Location: Gulberg, Lahore. "
            "CNIC: 35202-1234567-1. "
            "\nCase create karo aur 6-month follow-up bhi schedule karo."
        )

        print(f"📝 Query:\n{query1}\n")
        result1 = await run_with_retry(criminal_agent, query1)
        print("✅ [RESPONSE]")
        print(redact_pii(result1.final_output if hasattr(result1, "final_output") else str(result1)))
        print()

        # Test 2: Check pending follow-ups
        print("=" * 70)
        print("TEST 2: Check Pending Follow-ups")
        print("-" * 70)

        query2 = (
            "Kya koi cases hain jo 6 months se zyada ho gaye hain? "
            "Pending follow-ups check karo aur batao."
        )

        print(f"📝 Query:\n{query2}\n")
        result2 = await run_with_retry(criminal_agent, query2)
        print("✅ [RESPONSE]")
        print(result2.final_output if hasattr(result2, "final_output") else str(result2))
        print()

        # Test 3: Generate follow-up report
        print("=" * 70)
        print("TEST 3: Generate 6-Month Follow-up Report")
        print("-" * 70)

        query3 = (
            "Case CASE-12345 ki 6-month follow-up report generate karo. "
            "Evidence, duration, closure status sab chahiye."
        )

        print(f"📝 Query:\n{query3}\n")
        result3 = await run_with_retry(criminal_agent, query3)
        print("✅ [RESPONSE]")
        print(redact_pii(result3.final_output if hasattr(result3, "final_output") else str(result3)))
        print()

        # Test 4: Send follow-up reminder
        print("=" * 70)
        print("TEST 4: Send Follow-up Reminder to Police")
        print("-" * 70)

        query4 = (
            "Case CASE-12345 abhi tak khula hai aur 6 months ho gaye. "
            "Police ko follow-up reminder bhejo. "
            "Email: hafizalaibafaisal@gmail.com"
        )

        print(f"📝 Query:\n{query4}\n")
        result4 = await run_with_retry(criminal_agent, query4)
        print("✅ [RESPONSE]")
        print(result4.final_output if hasattr(result4, "final_output") else str(result4))
        print()

        # Test 5: Update case status
        print("=" * 70)
        print("TEST 5: Close Case After Follow-up")
        print("-" * 70)

        query5 = (
            "Case CASE-12345 ko band karo. "
            "Police ne case solve kar liya hai. "
            "Closure notes: Suspect arrested and convicted."
        )

        print(f"📝 Query:\n{query5}\n")
        result5 = await run_with_retry(criminal_agent, query5)
        print("✅ [RESPONSE]")
        print(result5.final_output if hasattr(result5, "final_output") else str(result5))
        print()

        # Test 6: Complex workflow - victim needs multiple handoffs
        print("=" * 70)
        print("TEST 6: Complex Case - Victim Needs Ambulance + Mental Support")
        print("-" * 70)

        query6 = (
            "Emergency: 28-year-old female victim of domestic violence. "
            "Multiple injuries, needs immediate ambulance. "
            "Location: Johar Town, Lahore (lat=31.4697, lon=74.2728). "
            "Patient is traumatized and crying uncontrollably - needs mental health support. "
            "\nKya karna chahiye? Full workflow chalo."
        )

        print(f"📝 Query:\n{query6}\n")
        result6 = await run_with_retry(criminal_agent, query6)
        print("✅ [RESPONSE - FULL WORKFLOW]")
        print(redact_pii(result6.final_output if hasattr(result6, "final_output") else str(result6)))
        print()

        # Summary
        print("=" * 70)
        print("\n📊 DEMO SUMMARY")
        print("-" * 70)
        print("✅ Total tests: 6")
        print(f"📝 Audit logs: {len(audit_logs)}")
        print(f"💾 Logs saved: {AUDIT_LOG_FILE}")
        print("\n🎯 Features Tested:")
        print("   ✅ Case creation with auto follow-up scheduling")
        print("   ✅ Pending follow-ups check")
        print("   ✅ Follow-up report generation")
        print("   ✅ Follow-up reminder to police")
        print("   ✅ Case closure after follow-up")
        print("   ✅ Complex multi-agent handoffs")
        print("\n🤖 6-Month Follow-up System: ACTIVE!")

        await orchestrator_mcp.cleanup()
        await domain_mcp.cleanup()


if __name__ == "__main__":
    asyncio.run(run_demo())