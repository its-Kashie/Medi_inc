# tracking_agent.py
import asyncio
import json
import os
import re
from datetime import datetime
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


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

# ===== AUDIT & TRACE LOGS =====
AUDIT_LOG_FILE = "audit_trace.json"
audit_logs = []

def log_decision(agent_name, action, reasoning, data=None, consent_token=None):
    """🧠 Reasoning Trace + 🕵️ Audit Control"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "reasoning": reasoning,
        "data": data or {},
        "consent_token": consent_token or "N/A"
    }
    audit_logs.append(entry)

    # Save to file
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(audit_logs, f, indent=2)

    print(f"📝 [AUDIT] {agent_name} → {action}")

# ===== PRIVACY FILTER =====
def redact_pii(text):
    """🔐 Privacy Filter - mask patient IDs, phone numbers, CNIC"""
    if not text:
        return text

    # Mask patient IDs (e.g., PATIENT-123 → PATIENT-***)
    text = re.sub(r'(PATIENT|MOTHER|AMB)-\d+', r'\1-***', text)

    # Mask phone numbers (e.g., +923001234567 → +9230012*****)
    text = re.sub(r'\+92\d{7}\d+', '+92*******', text)

    # Mask CNIC (e.g., 35202-1234567-1 → 35202-*******-*)
    text = re.sub(r'\d{5}-\d{7}-\d', '*****-*******-*', text)

    return text

# ===== RETRY LOGIC =====
async def run_with_retry(agent, query, max_retries=3):
    """🔄 Retry & Fallback logic"""
    for attempt in range(max_retries):
        try:
            result = await Runner.run(agent, query)
            return result
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print("❌ All retries failed, using degraded mode")
                # Degraded mode: return basic fallback
                return {"final_output": "System offline. SMS fallback activated. Contact 1122."}
            await asyncio.sleep(1)  # Wait before retry

# ===== MCP SERVER WITH DEGRADED MODE =====
async def connect_mcp_with_fallback(mcp_server):
    """📱 Degraded Mode - agar MCP fail ho to continue"""
    try:
        await mcp_server.connect()
        print("✅ MCP Server connected")
        return True
    except Exception as e:
        print(f"⚠️ MCP connection failed: {e}")
        print("📱 Degraded Mode: Using SMS fallback")
        return False


# ===== MCP SERVERS (2 servers for inter-agent communication) =====

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
#
# # ===== TRACKING AGENT WITH ENHANCED INSTRUCTIONS =====
# tracking_agent = Agent(
#     name="TrackingAgent",
#     model=gemini_model,
#     instructions=(
#         "You are a Lahore dispatch tracking agent with these capabilities:\n"
#         "🧠 REASONING: Always explain WHY you chose a specific ambulance/hospital\n"
#         "🔐 PRIVACY: Never share full patient IDs or phone numbers in responses\n"
#         "🌐 MULTILINGUAL: Respond in Urdu if user speaks Urdu, English otherwise\n"
#         "📱 DEGRADED MODE: If tools fail, provide SMS fallback (1122 or hospital contact)\n"
#         "🕵️ AUDIT: Every action is logged with reasoning trace\n"
#         "\nUse MCP tools to dispatch ambulances, find nearest hospitals, and release ambulances.\n"
#         "Format response with: 1) Reasoning 2) Action taken 3) Next steps"
#     ),
#     mcp_servers=[mcp_server]
# )
#

# ===== TRACKING AGENT =====
tracking_agent = Agent(
    name="TrackingAgent",
    model=gemini_model,
    instructions=(
        "You are the Emergency Tracking & Dispatch Agent for Lahore hospitals.\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🔄 INTER-AGENT HANDOFF SYSTEM (CRITICAL - READ FIRST)\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "STEP 1: CHECK INCOMING TASKS\n"
        "→ ALWAYS call check_my_tasks('tracking') at the START of every conversation\n"
        "→ Process any pending handoffs from other hospital_agents BEFORE handling new user requests\n"
        "→ If tasks found: complete them FIRST, then respond to user\n\n"

        "STEP 2: DETECT IF YOU NEED ANOTHER AGENT\n"
        "Handoff triggers (MUST use handoff_to_agent if detected):\n\n"

        "→ MATERNAL AGENT:\n"
        "  Keywords: pregnant, pregnancy, maternal, delivery, anc, postpartum, labor, baby\n"
        "  Example: 'Pregnant woman needs care' → handoff_to_agent(to_agent='maternal')\n\n"

        "→ PHARMACY AGENT:\n"
        "  Keywords: medicine, pharmacy, stock, prescription, supplements, iron, folic acid, drugs\n"
        "  Example: 'Check medicine stock' → handoff_to_agent(to_agent='pharmacy')\n\n"

        "→ MENTAL HEALTH AGENT:\n"
        "  Keywords: depression, anxiety, trauma, mental, stress, counseling, therapist, panic\n"
        "  Example: 'Patient showing anxiety' → handoff_to_agent(to_agent='mental')\n\n"

        "→ CRIMINAL AGENT:\n"
        "  Keywords: assault, suspicious injury, police, violence, abuse, attack, harassment\n"
        "  Example: 'Suspicious bruises' → handoff_to_agent(to_agent='criminal')\n\n"

        "STEP 3: EXECUTE HANDOFF\n"
        "When trigger detected, call:\n"
        "handoff_to_agent(\n"
        "    from_agent='tracking',\n"
        "    to_agent='<target_agent>',  # maternal/pharmacy/mental/criminal\n"
        "    task_type='<specific_task>',  # e.g., 'medicine_request', 'maternal_emergency'\n"
        "    context={\n"
        "        'location': {'lat': <lat>, 'lon': <lon>},\n"
        "        'patient_details': '<description>',\n"
        "        'medications_needed': ['<med1>', '<med2>'],  # if pharmacy\n"
        "        'emergency_type': '<type>',  # if maternal\n"
        "        'priority': 'high/normal/low'\n"
        "    },\n"
        "    priority='urgent'  # if emergency, else 'normal'\n"
        ")\n\n"

        "STEP 4: CONFIRM HANDOFF TO USER\n"
        "Tell user: '🔄 Handing off to [AGENT NAME] for specialized care...'\n"
        "Include handoff_id in response\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🚑 YOUR DOMAIN TOOLS (Ambulance & Emergency Dispatch)\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "USE THESE for your primary job:\n"
        "- dispatch_nearest_ambulance(lat, lon)\n"
        "  → Find and dispatch closest available ambulance\n"
        "  → Returns: ambulance_id, service, contact, distance, eta\n\n"

        "- release_ambulance(ambulance_id)\n"
        "  → Mark ambulance as available after task completion\n"
        "  → Call this when patient delivered or emergency resolved\n\n"

        "- nearest_hospital_fallback(lat, lon)\n"
        "  → Emergency fallback if ambulances unavailable\n"
        "  → Returns nearest hospital with contact info\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🧠 DECISION LOGIC\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "SCENARIO 1: Pure Emergency Dispatch\n"
        "User: 'Emergency at Mayo Hospital, location 31.58, 74.31'\n"
        "You: dispatch_nearest_ambulance(31.58, 74.31) → Done ✅\n\n"

        "SCENARIO 2: Emergency + Maternal Care\n"
        "User: 'Pregnant woman emergency at location 31.52, 74.35'\n"
        "You: \n"
        "  1. dispatch_nearest_ambulance(31.52, 74.35)\n"
        "  2. handoff_to_agent(to_agent='maternal', context=<pregnancy_details>)\n"
        "  3. Tell user both actions taken ✅\n\n"

        "SCENARIO 3: Post-Delivery Medicine Request\n"
        "User: 'Patient delivered, needs iron supplements and folic acid'\n"
        "You:\n"
        "  1. Acknowledge delivery\n"
        "  2. handoff_to_agent(to_agent='maternal', task_type='pharmacy_request')\n"
        "  3. Maternal agent will coordinate with pharmacy ✅\n\n"

        "SCENARIO 4: Only Medicine Request (No Emergency)\n"
        "User: 'Check pharmacy stock for iron supplements at Services Hospital'\n"
        "You: handoff_to_agent(to_agent='pharmacy') → Direct handoff ✅\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "📋 RESPONSE FORMAT (ALWAYS USE THIS STRUCTURE)\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "1️⃣ REASONING:\n"
        "   'I detected [keywords/trigger]. This requires [agent/action].'\n\n"

        "2️⃣ ACTION TAKEN:\n"
        "   '- Called dispatch_nearest_ambulance() → Ambulance MAYO-A1 dispatched'\n"
        "   '- Called handoff_to_agent() → Handoff to Maternal Agent (ID: HANDOFF-12345)'\n\n"

        "3️⃣ RESULT:\n"
        "   'Ambulance ETA: 6-8 minutes. Maternal specialist will coordinate further care.'\n\n"

        "4️⃣ NEXT STEPS:\n"
        "   'Please wait for ambulance arrival. Maternal agent will contact you for follow-up.'\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🔐 CRITICAL RULES\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "✅ DO:\n"
        "- ALWAYS check_my_tasks() first\n"
        "- Use handoff_to_agent() when ANY trigger keyword detected\n"
        "- Provide clear reasoning for every action\n"
        "- Respond in user's language (Urdu/English)\n"
        "- Redact sensitive info (full CNICs, phone numbers)\n"
        "- Include handoff_id in responses\n\n"

        "❌ DON'T:\n"
        "- Skip handoffs and try to handle pharmacy/maternal tasks yourself\n"
        "- Call pharmacy_request() directly - ALWAYS handoff to pharmacy agent\n"
        "- Ignore pending tasks from other hospital_agents\n"
        "- Share raw patient IDs or personal info\n"
        "- Respond without explaining reasoning\n\n"

        "🌐 MULTILINGUAL:\n"
        "- If user speaks Urdu/Roman Urdu → Respond in Urdu\n"
        "- If user speaks English → Respond in English\n"
        "- Mix is okay: 'Ambulance dispatch ho gaya hai. ETA: 6 minutes.'\n\n"

        "📱 DEGRADED MODE:\n"
        "- If MCP tools fail → Provide SMS fallback\n"
        "- Emergency hotline: 1122 (Rescue)\n"
        "- Always give hospital contact numbers\n\n"

        "═══════════════════════════════════════════════════════════════\n"
        "🎯 EXAMPLES\n"
        "═══════════════════════════════════════════════════════════════\n\n"

        "EXAMPLE 1:\n"
        "User: 'Pregnant patient at location 31.5204, 74.3587 needs iron supplements'\n"
        "You:\n"
        "1️⃣ REASONING: Detected 'pregnant' (maternal) + 'iron supplements' (pharmacy)\n"
        "2️⃣ ACTION: Calling handoff_to_agent(to_agent='maternal')\n"
        "3️⃣ RESULT: Handoff created (HANDOFF-1234567890) to Maternal Health Agent\n"
        "4️⃣ NEXT: Maternal agent will coordinate pharmacy stock check and prescription\n\n"

        "EXAMPLE 2:\n"
        "User: 'Emergency ambulance chahiye Mayo Hospital ke paas'\n"
        "You:\n"
        "1️⃣ REASONING: Pure emergency dispatch request\n"
        "2️⃣ ACTION: Calling dispatch_nearest_ambulance(31.5497, 74.3436)\n"
        "3️⃣ RESULT: Ambulance MAYO-A1 dispatched, ETA 7 minutes\n"
        "4️⃣ NEXT: Ambulance on the way. Contact: 042-9920-1409\n\n"

        "EXAMPLE 3:\n"
        "User: 'Patient showing severe anxiety after accident'\n"
        "You:\n"
        "1️⃣ REASONING: Detected 'anxiety' (mental health trigger)\n"
        "2️⃣ ACTION: Calling handoff_to_agent(to_agent='mental')\n"
        "3️⃣ RESULT: Handoff to Mental Health Agent (HANDOFF-9876543210)\n"
        "4️⃣ NEXT: Mental health specialist will assess and assign therapist\n\n"

        "═══════════════════════════════════════════════════════════════\n\n"

        "Remember: You are the COORDINATOR. Your job is to:\n"
        "1. Handle emergency ambulance dispatch (your expertise)\n"
        "2. Recognize when specialists are needed (maternal/pharmacy/mental/criminal)\n"
        "3. Handoff smoothly with full context\n"
        "4. Keep user informed about all actions\n\n"

        "Every message is logged and audited. Be transparent and thorough! 🚑"
    ),
    mcp_servers=[orchestrator_mcp, domain_mcp]
)

# ===== DEMO FUNCTION WITH ALL CAPABILITIES =====
async def run_demo():
    async with orchestrator_mcp, domain_mcp:
    # async with mcp_server:
        try:
            await orchestrator_mcp.connect()
            await domain_mcp.connect()
            print("✅ Both MCP servers connected\n")
            # await mcp_server.connect()
            # print("✅ MCP Connected\n")
        except Exception as e:
            print(f"⚠️ MCP failed: {e}\n")

        print("\n🚑 Tracking Agent Started with Enhanced Capabilities!\n")

        # Test 1: Dispatch with reasoning trace
        print("=" * 60)
        query1 = "Mayo Hospital ke paas emergency hai, patient PATIENT-12345, ambulance chahiye location 31.58, 74.31"

        log_decision(
            agent_name="TrackingAgent",
            action="dispatch_request_received",
            reasoning="Emergency request near Mayo Hospital received",
            data={"location": "31.58, 74.31", "patient_id": "PATIENT-12345"},
            consent_token="CONSENT-2024-001"
        )

        result1 = await run_with_retry(tracking_agent, query1)
        output1 = result1.final_output if hasattr(result1, "final_output") else str(result1)

        # Apply privacy filter
        filtered_output1 = redact_pii(output1)

        print("🔐 [PRIVACY FILTERED OUTPUT]")
        print(filtered_output1)
        print()

        log_decision(
            agent_name="TrackingAgent",
            action="ambulance_dispatched",
            reasoning="Nearest available ambulance selected based on distance",
            data={"output": filtered_output1}
        )

        # Test 2: Fallback hospital with retry
        print("=" * 60)
        query2 = "Agar MCP offline ho to nearest hospital bata do 31.50, 74.32, patient phone +923001234567"

        result2 = await run_with_retry(tracking_agent, query2)
        output2 = result2.final_output if hasattr(result2, "final_output") else str(result2)

        filtered_output2 = redact_pii(output2)
        print("🔐 [PRIVACY FILTERED OUTPUT]")
        print(filtered_output2)
        print()

        log_decision(
            agent_name="TrackingAgent",
            action="fallback_hospital_provided",
            reasoning="Degraded mode activated - provided nearest hospital contact",
            data={"output": filtered_output2}
        )

        # Test 3: Release ambulance
        print("=" * 60)
        query3 = "MAYO-A1 ambulance ab free ho gayi, release kar do"

        result3 = await run_with_retry(tracking_agent, query3)
        output3 = result3.final_output if hasattr(result3, "final_output") else str(result3)

        print("✅ [OUTPUT]")
        print(output3)
        print()

        log_decision(
            agent_name="TrackingAgent",
            action="ambulance_released",
            reasoning="Ambulance job completed, marked as available",
            data={"ambulance_id": "MAYO-A1"}
        )

        print("=" * 60)
        print(f"\n📊 Total audit logs: {len(audit_logs)}")
        print(f"💾 Logs saved to: {AUDIT_LOG_FILE}")

        await orchestrator_mcp.cleanup()
        await domain_mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(run_demo())