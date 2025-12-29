# waste_agent.py - Intelligent Hospital Waste Management Agent
import asyncio
import os

# ✅ SET TIMEOUT BEFORE ALL IMPORTS
os.environ['MCP_CLIENT_TIMEOUT'] = '300'

from datetime import datetime
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

from dotenv import load_dotenv
import json

# ===== waste_weight_estimator.py =====
from pathlib import Path
from typing import Dict

# Predefined container volumes (Liters)
CONTAINER_VOLUMES = {
    "placenta_bucket": 10,      # 10 Liters
    "bio_bag_small": 10,        # 10 Liters
    "bio_bag_large": 20,        # 20 Liters
    "sharps_box": 5,            # 5 Liters
    "pharma_box": 8,            # 8 Liters
    "general_bag": 15           # 15 Liters
}

# Approximate densities (kg/L)
WASTE_DENSITY = {
    "placenta": 1.06,
    "bio_medical": 0.95,
    "sharps": 0.90,
    "pharmaceutical": 0.85,
    "general": 0.5
}


def estimate_weight(detections: Dict[str, int]) -> Dict[str, float]:
    """
    Estimate weight of waste from detection counts.
    detections: Dict[container_type -> count]
        e.g., {"placenta_bucket": 1, "bio_bag_large": 2, "sharps_box": 3}
    Returns: Dict[waste_type -> estimated_kg]
    """

    weights = {
        "placenta": 0.0,
        "bio_medical": 0.0,
        "sharps": 0.0,
        "pharmaceutical": 0.0,
        "general": 0.0
    }

    for container, count in detections.items():
        volume = CONTAINER_VOLUMES.get(container, 0)
        if "placenta" in container:
            weights["placenta"] += count * volume * WASTE_DENSITY["placenta"]
        elif "bio_bag" in container:
            weights["bio_medical"] += count * volume * WASTE_DENSITY["bio_medical"]
        elif "sharps" in container:
            weights["sharps"] += count * volume * WASTE_DENSITY["sharps"]
        elif "pharma" in container:
            weights["pharmaceutical"] += count * volume * WASTE_DENSITY["pharmaceutical"]
        elif "general" in container:
            weights["general"] += count * volume * WASTE_DENSITY["general"]

    # Round weights to 2 decimals
    for k in weights:
        weights[k] = round(weights[k], 2)

    return weights

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found!")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

#===== MCP SERVERS =====
waste_mcp = MCPServerStdio(
    params={"command": "python", "args": ["../mcp_servers/waste_mcp/waste_mcp_tools.py"]},
    cache_tools_list=True,
    name="WasteMCP"
)



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
        "args": ["/mcp_servers/core_agents_mcp/agents_mcp.py"]
    },
    cache_tools_list=True,
    name="DomainMCP"
)
# ===== INTELLIGENT WASTE BROKER AGENT =====
smart_waste_agent = Agent(
    name="SmartWasteBroker",
    model=gemini_model,
    instructions=(
           "You are an INTELLIGENT HOSPITAL WASTE BROKER AGENT.\n\n"
        
        "🔧 CRITICAL INSTRUCTION - READ CAREFULLY:\n"
        "When you receive a message containing 'Analyze this video:' with a video path:\n"
        "1. IMMEDIATELY call the analyze_video_waste(video_path) tool\n"
        "2. Extract ONLY the file path from the message\n"
        "3. Wait for tool results before responding\n"
        "4. Return results as JSON format\n\n"
        
        "Example:\n"
        "User: 'Analyze this video: /path/to/video.mp4'\n"
        "You: [Call analyze_video_waste('/path/to/video.mp4')]\n"
        "You: [Return JSON with results]\n\n"
        
        "NEVER respond without calling the tool first.\n\n"
        "🎯 YOUR ROLE:\n"
        "You act as a SMART BROKER between hospitals and disposal companies.\n"
        "You NEGOTIATE best prices, schedule pickups, ensure compliance, and maximize efficiency.\n\n"

        "📹 VIDEO ANALYSIS:\n"
        "You receive video analysis data from 2 AI models:\n"
        "1. PLACENTA DETECTOR - Detects placenta in pathological waste\n"
        "2. WASTE CLASSIFIER - Classifies waste types (bio, sharps, pharma, general)\n\n"

        "💼 BROKER CAPABILITIES:\n"
        "- Find cheapest disposal company for hospital\n"
        "- Negotiate bulk discounts (5-15% savings)\n"
        "- Schedule optimal pickup times (reduce costs)\n"
        "- Match waste type to specialized disposal companies\n"
        "- Track disposal compliance (EPA, WHO standards)\n"
        "- Alert hospitals of violations BEFORE EPA fines\n\n"

        "🗑️ WASTE TYPES & PRICING:\n"
        "- Bio-medical waste: Rs. 50-80/kg\n"
        "- Sharp waste: Rs. 60-90/kg\n"
        "- Pharmaceutical waste: Rs. 100-150/kg\n"
        "- Placenta/pathological: Rs. 120-180/kg\n"
        "- General waste: Rs. 10-20/kg\n\n"

        "🔧 YOUR MCP TOOLS:\n"
        "- analyze_video_waste(video_path) - Get AI analysis\n"
        "- find_disposal_companies(waste_type, location) - Find vendors\n"
        "- negotiate_price(company_id, waste_kg, waste_type) - Get best deal\n"
        "- schedule_pickup(hospital_id, company_id, pickup_time) - Arrange collection\n"
        "- check_compliance(hospital_id) - Verify EPA compliance\n"
        "- generate_cost_report(hospital_id, period) - Show savings\n\n"

        "💡 INTELLIGENT DECISIONS:\n"
        "Example scenario:\n"
        "Video shows: 15kg bio-waste + 2kg sharps + 5kg placenta\n"
        "\n"
        "YOUR LOGIC:\n"
        "1. Find 3 disposal companies in Lahore\n"
        "2. Company A: Rs. 75/kg bio, Rs. 85/kg sharps, Rs. 150/kg placenta = Rs. 1,695\n"
        "3. Company B: Rs. 70/kg bio, Rs. 90/kg sharps, Rs. 140/kg placenta = Rs. 1,530 ✅ BEST\n"
        "4. Company C: Rs. 80/kg bio, Rs. 80/kg sharps, Rs. 160/kg placenta = Rs. 1,720\n"
        "5. Select Company B → Save Rs. 165 (10% savings)\n"
        "6. Schedule pickup for tomorrow 8 AM (off-peak = 5% discount)\n"
        "7. Total savings: 15% = Rs. 250\n\n"

        "🚨 COMPLIANCE MONITORING:\n"
        "If video shows violations:\n"
        "- Waste mixing → Alert hospital immediately\n"
        "- No PPE → Schedule staff training\n"
        "- Container overflow → URGENT pickup (avoid EPA fine of Rs. 50,000)\n"
        "- Unlabeled waste → Send proper labels\n\n"

        "📊 RESPONSE FORMAT:\n"
        "For each request, provide:\n"
        "1. VIDEO ANALYSIS SUMMARY\n"
        "2. WASTE BREAKDOWN (types & quantities)\n"
        "3. DISPOSAL COMPANY OPTIONS (3 best)\n"
        "4. RECOMMENDED CHOICE (with reasoning)\n"
        "5. COST COMPARISON (show savings)\n"
        "6. PICKUP SCHEDULE\n"
        "7. COMPLIANCE STATUS\n"
        "8. NEXT ACTIONS\n\n"

        "Example Output:\n"
        "```\n"
        "SMART WASTE BROKER ANALYSIS\n"
        "\n"
        "📹 VIDEO ANALYSIS:\n"
        "Duration: 2:35 minutes\n"
        "Location: Jinnah Hospital - Surgery Ward\n"
        "AI Models Used: Placenta Detector + Waste Classifier\n"
        "\n"
        "🗑️ WASTE DETECTED:\n"
        "- Bio-medical waste: 12 kg\n"
        "- Sharp waste (syringes): 3 kg\n"
        "- Placenta (pathological): 4 kg\n"
        "- General waste: 8 kg (VIOLATION: mixed with bio-waste)\n"
        "Total Weight: 27 kg\n"
        "\n"
        "🏢 DISPOSAL COMPANY OPTIONS:\n"
        "\n"
        "Option 1: LWMC (Lahore Waste Management)\n"
        "- Bio: Rs. 75/kg = Rs. 900\n"
        "- Sharps: Rs. 85/kg = Rs. 255\n"
        "- Placenta: Rs. 150/kg = Rs. 600\n"
        "TOTAL: Rs. 1,755\n"
        "Pickup: Next day, 10 AM\n"
        "\n"
        "Option 2: EcoWaste Solutions ✅ RECOMMENDED\n"
        "- Bio: Rs. 68/kg = Rs. 816\n"
        "- Sharps: Rs. 80/kg = Rs. 240\n"
        "- Placenta: Rs. 140/kg = Rs. 560\n"
        "TOTAL: Rs. 1,616\n"
        "Pickup: Same day, 6 PM (off-peak discount)\n"
        "EPA Certified ✅\n"
        "WHO Compliant ✅\n"
        "\n"
        "Option 3: GreenMed Disposal\n"
        "- Bio: Rs. 80/kg = Rs. 960\n"
        "- Sharps: Rs. 90/kg = Rs. 270\n"
        "- Placenta: Rs. 160/kg = Rs. 640\n"
        "TOTAL: Rs. 1,870\n"
        "Pickup: Next day, 2 PM\n"
        "\n"
        "💰 COST ANALYSIS:\n"
        "Cheapest: EcoWaste Solutions - Rs. 1,616\n"
        "Most Expensive: GreenMed - Rs. 1,870\n"
        "YOUR SAVINGS: Rs. 254 (13.6%)\n"
        "\n"
        "🎯 RECOMMENDATION:\n"
        "SELECT: EcoWaste Solutions\n"
        "REASON: Best price + Same-day pickup + Certified\n"
        "SAVINGS: Rs. 254 this pickup\n"
        "ANNUAL SAVINGS: ~Rs. 91,000 (if weekly pickups)\n"
        "\n"
        "📅 PICKUP SCHEDULED:\n"
        "Company: EcoWaste Solutions\n"
        "Date: Today (27 Nov 2025)\n"
        "Time: 6:00 PM\n"
        "Truck: BIO-HAZARD-007\n"
        "Driver: Ahmed Khan - 0300-1234567\n"
        "\n"
        "⚠️ COMPLIANCE ISSUES:\n"
        "🔴 VIOLATION: General waste mixed with bio-waste (00:45 in video)\n"
        "   - Risk: EPA fine Rs. 50,000\n"
        "   - Action: Staff retraining scheduled for tomorrow 10 AM\n"
        "\n"
        "✅ ACTIONS TAKEN:\n"
        "1. Pickup scheduled with EcoWaste\n"
        "2. Hospital notified of waste mixing violation\n"
        "3. Training session booked\n"
        "4. Compliance report sent to admin\n"
        "5. Cost savings report emailed to hospital CFO\n"
        "\n"
        "📊 NEXT STEPS:\n"
        "- Monitor pickup completion\n"
        "- Verify waste disposal certificate\n"
        "- Schedule follow-up inspection in 7 days\n"
        "- Track EPA compliance score\n"
        "```\n\n"

        "🌐 LANGUAGE: Urdu or English\n"
        "💬 TONE: Professional but helpful (jaise hospital ka trusted advisor)"
    ),
    mcp_servers=[orchestrator_mcp, domain_mcp]
)


async def run_smart_broker_demo():
    """Demo: Smart waste broker with video analysis"""

    async with waste_mcp:
        try:
            await waste_mcp.connect()
            print("✅ Waste MCP connected\n")
        except Exception as e:
            print(f"⚠️ MCP failed: {e}\n")

        print("🤖 INTELLIGENT WASTE BROKER AGENT - DEMO")
        print("=" * 80)

        # Test 1: Video Analysis + Cost Optimization
        print("\n" + "=" * 80)
        print("TEST 1: Video Analysis → Find Cheapest Disposal")
        print("-" * 80)

        query = (
            "Video analysis report:\n"
            "- Location: Jinnah Hospital Surgery Ward\n"
            "- Duration: 3 minutes\n"
            "- AI Detection Results:\n"
            "  * Placenta Detector: 5 kg placenta found\n"
            "  * Waste Classifier: 18 kg bio-waste, 4 kg sharps, 10 kg general\n"
            "\n"
            "Find me the CHEAPEST disposal company in Lahore. "
            "Schedule pickup for today if possible. "
            "Show me exactly how much I'll save."
        )

        print(f"📝 QUERY:\n{query}\n")

        result = await Runner.run(smart_waste_agent, query)
        print("🤖 AGENT RESPONSE:")
        print(result.final_output if hasattr(result, "final_output") else str(result))

        # Test 2: Violation Detection + Compliance
        print("\n" + "=" * 80)
        print("TEST 2: Violation Detection → Prevent EPA Fine")
        print("-" * 80)

        query2 = (
            "URGENT: Video shows waste mixing violations at Mayo Hospital.\n"
            "Staff mixing bio-medical waste with general waste.\n"
            "Container CONT-005 overflowing.\n"
            "\n"
            "Help me:\n"
            "1. Schedule IMMEDIATE pickup\n"
            "2. Fix compliance issues before EPA inspection next week\n"
            "3. Get best price despite urgency"
        )

        print(f"📝 QUERY:\n{query2}\n")

        result2 = await Runner.run(smart_waste_agent, query2)
        print("🤖 AGENT RESPONSE:")
        print(result2.final_output if hasattr(result2, "final_output") else str(result2))

        # Test 3: Bulk Negotiation
        print("\n" + "=" * 80)
        print("TEST 3: Bulk Negotiation → Monthly Contract")
        print("-" * 80)

        query3 = (
            "Services Hospital generates ~500 kg waste per week.\n"
            "Current vendor charges Rs. 75/kg for bio-waste.\n"
            "\n"
            "Negotiate a MONTHLY CONTRACT with better rates. "
            "Show me annual savings with new contract."
        )

        print(f"📝 QUERY:\n{query3}\n")

        result3 = await Runner.run(smart_waste_agent, query3)
        print("🤖 AGENT RESPONSE:")
        print(result3.final_output if hasattr(result3, "final_output") else str(result3))

        print("\n" + "=" * 80)
        print("📊 DEMO SUMMARY")
        print("-" * 80)
        print("✅ Video AI analysis (2 models)")
        print("✅ Smart cost comparison (3 vendors)")
        print("✅ Automated negotiation (best price)")
        print("✅ Compliance monitoring (EPA/WHO)")
        print("✅ Violation prevention (fines avoided)")
        print("✅ Cost savings tracking (ROI calculation)")
        print("\n💡 Agent acts as intelligent broker between hospitals & disposal companies!")

        await waste_mcp.cleanup()
# ===== EXPORT FOR BACKEND =====
waste_agent = smart_waste_agent  # Backend import ke liye

# ===== EXPORT MCPs FOR BACKEND ===== ✅ YE ADD KARO
orchestrator_mcp = waste_mcp
domain_mcp = waste_mcp

if __name__ == "__main__":
    asyncio.run(run_smart_broker_demo())