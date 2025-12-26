# # criminal_agent.py - Complete Criminal Case Agent
# import asyncio
# import json
# import os
# import re
# import smtplib
# from datetime import datetime
# from email.message import EmailMessage
# from openai import AsyncOpenAI
# from agents import Agent, Runner, OpenAIChatCompletionsModel
# from agents.mcp import MCPServerStdio
# import random
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
# AUDIT_LOG_FILE = "criminal_audit.json"
# audit_logs = []
#
# def log_decision(agent_name, action, reasoning, data=None, consent_token=None):
#     """🧠 Audit logging with consent"""
#     entry = {
#         "timestamp": datetime.now().isoformat(),
#         "agent": agent_name,
#         "action": action,
#         "reasoning": reasoning,
#         "data": data or {},
#         "consent_token": consent_token or "N/A"
#     }
#     audit_logs.append(entry)
#     with open(AUDIT_LOG_FILE, "w") as f:
#         json.dump(audit_logs, f, indent=2)
#     print(f"📝 [AUDIT] {agent_name} → {action}")
#
# # ===== PRIVACY FILTER (Enhanced for criminal cases) =====
# def redact_pii(text):
#     """🔐 Privacy Filter - Extra protection for criminal cases"""
#     if not text:
#         return text
#
#     # Mask case IDs
#     text = re.sub(r'(CASE|VICTIM|SUSPECT)-\d+', r'\1-***', text)
#
#     # Mask patient/victim IDs
#     text = re.sub(r'(PATIENT|VICTIM)-\d+', r'\1-***', text)
#
#     # Mask phone numbers
#     text = re.sub(r'\+92\d{7}\d+', '+92*******', text)
#
#     # Mask CNIC
#     text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)
#
#     # Mask email
#     text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '***@***.com', text)
#
#     # Mask addresses (basic)
#     text = re.sub(r'House #\d+', 'House #***', text)
#
#     return text
#
# def pseudonymize_evidence(evidence_data):
#     """Pseudonymize sensitive evidence before transfer"""
#     if isinstance(evidence_data, dict):
#         pseudonymized = {}
#         for key, value in evidence_data.items():
#             if key in ["victim_name", "suspect_name", "witness_name"]:
#                 pseudonymized[key] = f"REDACTED_{key.upper()}"
#             elif key in ["cnic", "phone"]:
#                 pseudonymized[key] = "REDACTED"
#             else:
#                 pseudonymized[key] = value
#         return pseudonymized
#     return evidence_data
#
# # ===== LOCAL CASE DATABASE =====
# CASES_FILE = "criminal_cases.json"
# EVIDENCE_FILE = "criminal_evidence.json"
#
# def load_cases():
#     if os.path.exists(CASES_FILE):
#         with open(CASES_FILE, "r") as f:
#             return json.load(f)
#     return []
#
# def save_cases(cases):
#     with open(CASES_FILE, "w") as f:
#         json.dump(cases, f, indent=2)
#
# def load_evidence():
#     if os.path.exists(EVIDENCE_FILE):
#         with open(EVIDENCE_FILE, "r") as f:
#             return json.load(f)
#     return []
#
# def save_evidence(evidence_list):
#     with open(EVIDENCE_FILE, "w") as f:
#         json.dump(evidence_list, f, indent=2)
#
# # ===== POLICE JURISDICTIONS DATABASE =====
# POLICE_JURISDICTIONS = {
#     "Lahore_City": {
#         "station_name": "Civil Lines Police Station",
#         "contact": "+92423456789",
#         "email": "hafizalaibafaisal@gmail.com",
#         "jurisdiction": ["Gulberg", "Model Town", "Garden Town"]
#     },
#     "Lahore_Cantt": {
#         "station_name": "Cantonment Police Station",
#         "contact": "+92423456790",
#         "email": "jiniewinie000@gmail.com",
#         "jurisdiction": ["Cantt", "Mall Road", "Cavalry Ground"]
#     },
#     "Lahore_Iqbal": {
#         "station_name": "Iqbal Town Police Station",
#         "contact": "+92423456791",
#         "email": "ismatabubakar6@gmail.com",
#         "jurisdiction": ["Iqbal Town", "Johar Town", "Wapda Town"]
#     }
# }
#
# def get_jurisdiction(location_area):
#     """Find appropriate police jurisdiction"""
#     for jurisdiction_id, details in POLICE_JURISDICTIONS.items():
#         if any(area.lower() in location_area.lower() for area in details["jurisdiction"]):
#             return jurisdiction_id, details
#
#     # Default to Lahore City
#     return "Lahore_City", POLICE_JURISDICTIONS["Lahore_City"]
#
# # ===== LOCAL CRIMINAL CASE FUNCTIONS =====
#
# # # ===== MCP SERVER =====
# # mcp_server = MCPServerStdio(
# #     params={
# #         "command": "python",
# #         "args": ["agents_mcp.py"]
# #     },
# #     cache_tools_list=True,
# #     name="CriminalMCP"
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
# # # ===== CRIMINAL CASE AGENT =====
# # criminal_agent = Agent(
# #     name="CriminalCaseAgent",
# #     model=gemini_model,
# #     instructions=(
# #         "You are an autonomous criminal case detection and reporting agent for Pakistan's healthcare system.\n\n"
# #         "Your role is to detect violence, harassment, and suspicious injury cases from hospital records, "
# #         "auto-report to appropriate police jurisdictions, and coordinate evidence transfer.\n\n"
# #         "🧠 Available capabilities (tools via MCP):\n"
# #         "- Classify injuries as suspicious/violence/harassment using AI\n"
# #         "- Auto-report critical cases to police (with victim privacy protection)\n"
# #         "- Verify identity via NADRA integration\n"
# #         "- Collect and manage medical evidence\n"
# #         "- Transfer evidence to forensic departments with chain of custody\n"
# #         "- Coordinate with police jurisdictions based on location\n\n"
# #         "🔐 CRITICAL PRIVACY RULES:\n"
# #         "- ALWAYS pseudonymize victim data before police reports\n"
# #         "- NEVER share full victim names, CNIC, or addresses externally\n"
# #         "- Maintain chain of custody for all evidence\n"
# #         "- Log every action with consent tokens\n\n"
# #         "⚖️ AUTO-REPORT TRIGGERS:\n"
# #         "- Sexual violence or harassment (immediate report)\n"
# #         "- Multiple injuries suggesting assault (immediate report)\n"
# #         "- Gunshot/stab wounds (immediate report)\n"
# #         "- Burn injuries with suspicious circumstances (immediate report)\n"
# #         "- Domestic violence indicators (immediate report)\n\n"
# #         "🌐 Language: Respond in Urdu or English.\n"
# #         "📧 Notifications: Send alerts to police and hospital management.\n\n"
# #         "💡 Decision Flow:\n"
# #         "1. Analyze injury record → classify using AI\n"
# #         "2. If suspicious → create case report\n"
# #         "3. If critical → auto-report to police (pseudonymized)\n"
# #         "4. Collect medical evidence → maintain chain of custody\n"
# #         "5. Transfer evidence to forensics when requested\n"
# #         "6. Verify identity via NADRA if needed\n\n"
# #         "📋 Response Format:\n"
# #         "1) Reasoning: Why this case was flagged\n"
# #         "2) Action: What was done (report, evidence collection, etc.)\n"
# #         "3) Privacy Measures: How victim data was protected\n"
# #         "4) Next Steps: Recommendations for hospital/police"
# #     ),
# #     mcp_servers=[mcp_server]
# # )
#
# # ===== CRIMINAL CASE AGENT =====
# criminal_agent = Agent(
#     name="CriminalCaseAgent",
#     model=gemini_model,
#     instructions=(
#         "You are a criminal case detection agent for Pakistan.\n\n"
#
#         "🤝 ORCHESTRATOR TOOLS (inter-agent communication):\n"
#         "- handoff_to_agent(from_agent='criminal', to_agent, task_type, context, priority)\n"
#         "  → Victim needs ambulance? → handoff to 'tracking' agent\n"
#         "  → Victim needs mental support? → handoff to 'mental' agent\n"
#         "- check_my_tasks(agent_name='criminal')\n"
#         "  → Check for case reports from other agents\n"
#         "- complete_task(handoff_id, result, completed_by='criminal')\n"
#         "  → Complete tasks\n"
#         "- query_agent_capabilities(agent_name)\n"
#         "  → Check capabilities\n\n"
#
#         "⚡ WORKFLOW:\n"
#         "1. Start: check_my_tasks('criminal')\n"
#         "2. Classify injury → if suspicious, create case\n"
#         "3. Critical case? → report_to_police()\n"
#         "4. Victim trauma? → handoff_to_agent('criminal', 'mental', 'trauma_support', {...}, 'high')\n\n"
#
#         "⚖️ YOUR DOMAIN TOOLS:\n"
#         "- classify_injury_local(injury_notes, injury_type)\n"
#         "- create_case_report(patient_id, injury_notes, injury_type, location, cnic, victim_name)\n"
#         "- report_to_police(case_id, case_data)\n"
#         "- verify_identity_nadra(cnic)\n"
#         "- collect_medical_evidence(case_id, evidence_type, evidence_notes)\n"
#         "- transfer_evidence_to_forensics(evidence_id, case_id)\n"
#         "- get_police_jurisdiction(location)\n"
#         "- pseudonymize_case_data(case_data)\n\n"
#
#         "🔐 CRITICAL PRIVACY:\n"
#         "- ALWAYS pseudonymize before police reports\n"
#         "- NEVER share victim names, CNIC externally\n"
#         "- Maintain chain of custody\n"
#         "- Log with consent tokens\n\n"
#
#         "⚖️ AUTO-REPORT TRIGGERS:\n"
#         "- Sexual violence (immediate)\n"
#         "- Multiple assault injuries (immediate)\n"
#         "- Gunshot/stab wounds (immediate)\n"
#         "- Burn injuries (suspicious)\n"
#         "- Domestic violence (immediate)\n\n"
#
#         "🌐 Language: Urdu or English\n\n"
#
#         "📋 Format: 1) Reasoning 2) Action 3) Privacy Measures 4) Next Steps"
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
#                 return {"final_output": "System offline. Manual police reporting required."}
#             await asyncio.sleep(1)
#
# # ===== DEMO (LLM-DRIVEN - Agent decides when to use tools) =====
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
#         print("⚖️ Criminal Case Agent Started - LLM Autonomous Decision Testing!\n")
#         print("=" * 70)
#         print("🤖 Agent will decide which MCP tools to call based on queries\n")
#
#         # Test 1: LLM should classify injury and create case
#         print("=" * 70)
#         print("TEST 1: Suspicious Assault - LLM Creates Case")
#         print("-" * 70)
#
#         query1 = (
#             "Emergency room mein ek patient aya hai - PATIENT-001. "
#             "Patient ki medical report kehti hai: Multiple blunt trauma injuries to head and torso. "
#             "Patient reports being beaten by multiple attackers with wooden sticks. "
#             "Location: Gulberg, Lahore. "
#             "CNIC: 35202-1234567-1. "
#             "Kya ye suspicious case hai? Agar haan to proper case report banao aur zaroorat ho to police ko report karo."
#         )
#
#         print(f"📝 User Query:\n{query1}\n")
#
#         result1 = await run_with_retry(criminal_agent, query1)
#         output1 = result1.final_output if hasattr(result1, "final_output") else str(result1)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output1))
#         print()
#
#         # Test 2: LLM should detect critical case and auto-report
#         print("=" * 70)
#         print("TEST 2: Sexual Violence - LLM Auto-Reports")
#         print("-" * 70)
#
#         query2 = (
#             "URGENT CASE - Patient ID: PATIENT-002 "
#             "Medical examination report: Patient reports rape and sexual assault. "
#             "Physical examination shows signs of forced trauma. "
#             "Location: Model Town, Lahore. "
#             "Ye bohot serious case hai. Tum kya action loge? "
#             "Police ko report karni chahiye immediately?"
#         )
#
#         print(f"📝 User Query:\n{query2}\n")
#
#         result2 = await run_with_retry(criminal_agent, query2)
#         output2 = result2.final_output if hasattr(result2, "final_output") else str(result2)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output2))
#         print()
#
#         # Test 3: LLM should verify identity via NADRA
#         print("=" * 70)
#         print("TEST 3: Identity Verification - LLM Calls NADRA")
#         print("-" * 70)
#
#         query3 = (
#             "Ek criminal case hai jisme victim ki identity verify karni hai. "
#             "CNIC number: 35202-1234567-1. "
#             "NADRA se check karo ye valid CNIC hai ya nahi. "
#             "Case ID: CASE-12345 ke liye verification chahiye."
#         )
#
#         print(f"📝 User Query:\n{query3}\n")
#
#         result3 = await run_with_retry(criminal_agent, query3)
#         output3 = result3.final_output if hasattr(result3, "final_output") else str(result3)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output3))
#         print()
#
#         # Test 4: LLM should collect evidence
#         print("=" * 70)
#         print("TEST 4: Evidence Collection - LLM Collects Medical Evidence")
#         print("-" * 70)
#
#         query4 = (
#             "Case CASE-12345 ke liye medical evidence collect karni hai. "
#             "Hospital ne patient ki multiple photographs li hain jo head aur torso injuries show karti hain. "
#             "Visible bruising aur lacerations hain. "
#             "Evidence type: photographs. "
#             "Ye evidence properly document karo with chain of custody."
#         )
#
#         print(f"📝 User Query:\n{query4}\n")
#
#         result4 = await run_with_retry(criminal_agent, query4)
#         output4 = result4.final_output if hasattr(result4, "final_output") else str(result4)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output4))
#         print()
#
#         # Test 5: LLM should transfer evidence to forensics
#         print("=" * 70)
#         print("TEST 5: Forensic Transfer - LLM Transfers Evidence")
#         print("-" * 70)
#
#         query5 = (
#             "Evidence ID EVID-54321 ko forensic department ko transfer karna hai. "
#             "Case ID: CASE-12345. "
#             "Chain of custody update karke evidence forensics ko bhejo. "
#             "Report kab tak ayegi?"
#         )
#
#         print(f"📝 User Query:\n{query5}\n")
#
#         result5 = await run_with_retry(criminal_agent, query5)
#         output5 = result5.final_output if hasattr(result5, "final_output") else str(result5)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output5))
#         print()
#
#         # Test 6: Complex scenario - LLM decides multiple actions
#         print("=" * 70)
#         print("TEST 6: Complex Emergency - LLM Autonomous Multi-Step Decision")
#         print("-" * 70)
#
#         query6 = (
#             "Emergency room mein ek patient aya hai jisko knife se bohot zyada injuries hain. "
#             "Patient kahta hai usko 3 log ne attack kiya tha Johar Town mai. "
#             "Patient ka CNIC: 35202-9876543-2. "
#             "Injuries: Multiple stab wounds on chest and abdomen. "
#             "\nMujhe batao:\n"
#             "1. Ye case suspicious hai?\n"
#             "2. Police ko report karni chahiye?\n"
#             "3. Kaunsa police station contact karna chahiye?\n"
#             "4. Evidence collection zaruri hai?\n"
#             "5. NADRA se identity verify karni chahiye?\n"
#             "\nSab kuch step by step karo aur har decision ki reasoning do."
#         )
#
#         print(f"📝 User Query:\n{query6}\n")
#
#         result6 = await run_with_retry(criminal_agent, query6)
#         output6 = result6.final_output if hasattr(result6, "final_output") else str(result6)
#
#         print("✅ [LLM RESPONSE - FULL AUTONOMOUS WORKFLOW]")
#         print(redact_pii(output6))
#         print()
#
#         # Test 7: Non-suspicious case - LLM should NOT trigger tools
#         print("=" * 70)
#         print("TEST 7: Non-Suspicious Case - LLM Should Skip Reporting")
#         print("-" * 70)
#
#         query7 = (
#             "Patient PATIENT-007 hospital aya hai with minor bruise on arm. "
#             "Patient says he fell from his bicycle. "
#             "Injury notes: Small bruise, no signs of assault or violence. "
#             "Kya ye case suspicious hai? Police ko report karni chahiye?"
#         )
#
#         print(f"📝 User Query:\n{query7}\n")
#
#         result7 = await run_with_retry(criminal_agent, query7)
#         output7 = result7.final_output if hasattr(result7, "final_output") else str(result7)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output7))
#         print()
#
#         # Test 8: Jurisdiction query - LLM finds police station
#         print("=" * 70)
#         print("TEST 8: Jurisdiction Lookup - LLM Finds Police Station")
#         print("-" * 70)
#
#         query8 = (
#             "Ek crime Wapda Town, Lahore mein hui hai. "
#             "Mujhe batao kaunsa police station is area ka jurisdiction handle karta hai? "
#             "Contact number bhi chahiye."
#         )
#
#         print(f"📝 User Query:\n{query8}\n")
#
#         result8 = await run_with_retry(criminal_agent, query8)
#         output8 = result8.final_output if hasattr(result8, "final_output") else str(result8)
#
#         print("✅ [LLM RESPONSE]")
#         print(output8)
#         print()
#
#         # Test 9: Data pseudonymization - LLM protects privacy
#         print("=" * 70)
#         print("TEST 9: Privacy Protection - LLM Pseudonymizes Data")
#         print("-" * 70)
#
#         query9 = (
#             "Ek case report police ko bhejna hai lekin victim ki privacy protect karni hai. "
#             "Case data hai:\n"
#             "- Victim name: Ahmed Ali\n"
#             "- CNIC: 35202-1234567-1\n"
#             "- Phone: +923001234567\n"
#             "- Address: House #123, Street 5, Gulberg\n"
#             "- Injury: Knife attack\n"
#             "\nIs data ko pseudonymize karo taake police ko bhej sakte hain "
#             "lekin victim ki identity protected rahe."
#         )
#
#         print(f"📝 User Query:\n{query9}\n")
#
#         result9 = await run_with_retry(criminal_agent, query9)
#         output9 = result9.final_output if hasattr(result9, "final_output") else str(result9)
#
#         print("✅ [LLM RESPONSE]")
#         print(redact_pii(output9))
#         print()
#
#         # Summary
#         print("=" * 70)
#         print("\n📊 DEMO SUMMARY")
#         print("-" * 70)
#         print(f"✅ Total tests run: 9")
#         print(f"📝 Total audit logs: {len(audit_logs)}")
#         print(f"💾 Logs saved to: {AUDIT_LOG_FILE}")
#         print("\n🎯 Agent Capabilities Tested:")
#         print("   ✅ Injury classification (AI-powered)")
#         print("   ✅ Case creation with auto-report decision")
#         print("   ✅ Police reporting with privacy protection")
#         print("   ✅ NADRA identity verification")
#         print("   ✅ Medical evidence collection")
#         print("   ✅ Evidence transfer to forensics")
#         print("   ✅ Multi-step autonomous decision making")
#         print("   ✅ Non-suspicious case handling (no false reports)")
#         print("   ✅ Jurisdiction lookup")
#         print("   ✅ Data pseudonymization")
#         print("\n🤖 LLM decided ALL tool calls autonomously!")
#
#         await orchestrator_mcp.cleanup()
#         await domain_mcp.cleanup()
#
# if __name__ == "__main__":
#     asyncio.run(run_demo())


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
        "args": ["agent_orchestrator_mcp.py"]
    },
    cache_tools_list=True,
    name="OrchestratorMCP"
)

domain_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": ["agents_mcp.py"]
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