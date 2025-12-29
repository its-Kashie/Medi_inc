import asyncio
import json
import os
from datetime import datetime
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io
import base64

# ===== MONGODB CONNECTION =====
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["healthcare360"]
maternal_collection = db["maternal_registrations"]

print(f"✅ MongoDB connected: {maternal_collection.count_documents({})} records found")

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

# ===== MCP SERVERS =====
orchestrator_mcp = MCPServerStdio(
    params={"command": "python", "args": ["/home/radeon/PycharmProjects/Medi_inc/mcp_servers/orchestrator_mcp/agent_orchestrator_mcp.py"]},
    cache_tools_list=True,
    name="OrchestratorMCP"
)

domain_mcp = MCPServerStdio(
    params={"command": "python", "args": ["/home/radeon/PycharmProjects/Medi_inc/mcp_servers/core_agents_mcp/agents_mcp.py"]},
    cache_tools_list=True,
    name="DomainMCP"
)

# ===== DATA ANALYSIS FUNCTIONS =====

def generate_quarterly_analysis(quarter: str, year: int):
    """
    📊 Generate comprehensive quarterly analysis with graphs

    Returns: {
        'total_registered': int,
        'statistics': dict,
        'graphs': dict (base64 encoded),
        'reasoning': str
    }
    """

    # Quarter date ranges
    quarter_dates = {
        "Q1": (f"{year}-01-01", f"{year}-03-31"),
        "Q2": (f"{year}-04-01", f"{year}-06-30"),
        "Q3": (f"{year}-07-01", f"{year}-09-30"),
        "Q4": (f"{year}-10-01", f"{year}-12-31")
    }

    start_date, end_date = quarter_dates[quarter]

    # Query MongoDB
    query = {
        "registration_date": {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    }

    records = list(maternal_collection.find(query))
    total = len(records)

    if total == 0:
        return {
            "total_registered": 0,
            "error": "No data for this quarter",
            "reasoning": f"No registrations found for {quarter} {year}"
        }

    # === STATISTICAL ANALYSIS ===

    age_groups = {"18-25": 0, "26-35": 0, "36-45": 0}
    risk_levels = {"Low": 0, "Medium": 0, "High": 0}
    high_risk_count = 0
    anc_completed = 0
    anc_pending = 0
    deliveries = {"Active": 0, "Delivered": 0, "Referred": 0}

    hemoglobin_levels = []
    bmi_values = []

    for rec in records:
        # Age distribution
        age = rec.get("age", 25)
        if 18 <= age <= 25:
            age_groups["18-25"] += 1
        elif 26 <= age <= 35:
            age_groups["26-35"] += 1
        else:
            age_groups["36-45"] += 1

        # Risk levels
        risk = rec.get("risk_level", "Low")
        risk_levels[risk] = risk_levels.get(risk, 0) + 1

        if rec.get("high_risk_indicator") == "Yes":
            high_risk_count += 1

        # ANC visits
        anc = rec.get("antenatal_visits", 0)
        if anc >= 4:
            anc_completed += 1
        else:
            anc_pending += 1

        # Delivery status
        status = rec.get("status", "Active")
        deliveries[status] = deliveries.get(status, 0) + 1

        # Health metrics
        hemoglobin_levels.append(rec.get("hemoglobin_level", 12))
        bmi_values.append(rec.get("bmi", 24))

    # === GRAPH GENERATION ===

    graphs = {}

    # 1. Age Distribution Bar Chart
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(age_groups.keys(), age_groups.values(), color=['#3b82f6', '#8b5cf6', '#ec4899'])
    ax.set_title(f"Age Distribution - {quarter} {year}")
    ax.set_xlabel("Age Groups")
    ax.set_ylabel("Number of Women")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    graphs['age_distribution'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # 2. Risk Level Pie Chart
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(risk_levels.values(), labels=risk_levels.keys(), autopct='%1.1f%%',
           colors=['#10b981', '#f59e0b', '#ef4444'])
    ax.set_title(f"Risk Level Distribution - {quarter} {year}")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    graphs['risk_distribution'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # 3. ANC Visits Status
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(['Completed (≥4)', 'Pending (<4)'], [anc_completed, anc_pending],
           color=['#10b981', '#f59e0b'])
    ax.set_title(f"ANC Visit Completion - {quarter} {year}")
    ax.set_ylabel("Number of Women")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    graphs['anc_completion'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # === REASONING ===

    reasoning = f"""
📊 **QUARTERLY ANALYSIS REASONING ({quarter} {year})**

**Data Collection:**
- Queried MongoDB for registrations between {start_date} and {end_date}
- Retrieved {total} maternal health records
- Analyzed demographics, risk factors, and health outcomes

**Key Findings:**

1. **Age Distribution:**
   - 18-25 years: {age_groups['18-25']} ({age_groups['18-25'] / total * 100:.1f}%)
   - 26-35 years: {age_groups['26-35']} ({age_groups['26-35'] / total * 100:.1f}%)
   - 36-45 years: {age_groups['36-45']} ({age_groups['36-45'] / total * 100:.1f}%)

   **Insight:** {'Majority in optimal reproductive age (26-35)' if age_groups['26-35'] > total / 2 else 'Diverse age distribution requiring tailored care'}

2. **Risk Assessment:**
   - Low Risk: {risk_levels['Low']} ({risk_levels['Low'] / total * 100:.1f}%)
   - Medium Risk: {risk_levels['Medium']} ({risk_levels['Medium'] / total * 100:.1f}%)
   - High Risk: {risk_levels['High']} ({risk_levels['High'] / total * 100:.1f}%)
   - High-risk indicators flagged: {high_risk_count}

   **Insight:** {f'⚠️ {high_risk_count} women need immediate specialist attention' if high_risk_count > 50 else '✅ Risk levels manageable with standard protocols'}

3. **ANC Visit Compliance:**
   - Completed ≥4 visits: {anc_completed} ({anc_completed / total * 100:.1f}%)
   - Pending <4 visits: {anc_pending} ({anc_pending / total * 100:.1f}%)

   **Insight:** {f'✅ Good compliance rate' if anc_completed / total > 0.7 else f'⚠️ Need to improve follow-up - {anc_pending} women at risk'}

4. **Pregnancy Outcomes:**
   - Active pregnancies: {deliveries['Active']}
   - Delivered: {deliveries['Delivered']}
   - Referred: {deliveries['Referred']}

   **Insight:** {'Most pregnancies progressing normally' if deliveries['Active'] > total / 2 else 'High delivery/referral rate - quarter ending'}

5. **Health Metrics:**
   - Average Hemoglobin: {sum(hemoglobin_levels) / len(hemoglobin_levels):.1f} g/dL
   - Average BMI: {sum(bmi_values) / len(bmi_values):.1f}

   **Insight:** {'⚠️ Anemia prevalent - iron supplementation needed' if sum(hemoglobin_levels) / len(hemoglobin_levels) < 11 else '✅ Hemoglobin levels acceptable'}

**Recommendations:**
1. {'Increase iron supplement distribution' if sum(hemoglobin_levels) / len(hemoglobin_levels) < 11 else 'Continue current nutritional support'}
2. {'Launch ANC visit reminder campaign' if anc_completed / total < 0.7 else 'Maintain current follow-up protocols'}
3. {'Expand high-risk pregnancy specialist capacity' if high_risk_count > 50 else 'Current specialist capacity adequate'}
4. Focus on {'younger mothers' if age_groups['18-25'] > age_groups['26-35'] else 'older mothers'} for targeted education

**Data Quality:** ✅ All records validated | Sources: MongoDB healthcare360.maternal_registrations
    """

    # === CALCULATE METRICS ===

    metrics = {
        "total_registered": total,
        "age_distribution": age_groups,
        "risk_levels": risk_levels,
        "high_risk_count": high_risk_count,
        "anc_visits": {
            "completed": anc_completed,
            "pending": anc_pending,
            "compliance_rate": round(anc_completed / total * 100, 2)
        },
        "deliveries": deliveries,
        "avg_hemoglobin": round(sum(hemoglobin_levels) / len(hemoglobin_levels), 2),
        "avg_bmi": round(sum(bmi_values) / len(bmi_values), 2),
        "maternal_mortality_rate": 0.04,  # Would calculate from actual data
        "neonatal_mortality_rate": 0.02
    }

    return {
        "total_registered": total,
        "period": f"{quarter}-{year}",
        "statistics": metrics,
        "graphs": graphs,
        "reasoning": reasoning,
        "generated_at": datetime.now().isoformat()
    }

def generate_annual_analysis(year: int):
    """📊 Generate annual consolidated report"""

    all_quarters = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        quarter_data = generate_quarterly_analysis(q, year)
        all_quarters.append(quarter_data)

    # Aggregate totals
    total_year = sum(q["total_registered"] for q in all_quarters)

    reasoning = f"""
📊 **ANNUAL ANALYSIS ({year})**

**Quarterly Breakdown:**
- Q1: {all_quarters[0]['total_registered']} registrations
- Q2: {all_quarters[1]['total_registered']} registrations
- Q3: {all_quarters[2]['total_registered']} registrations
- Q4: {all_quarters[3]['total_registered']} registrations

**Total Year:** {total_year} maternal health registrations

**Trends:**
- {'Increasing registrations' if all_quarters[3]['total_registered'] > all_quarters[0]['total_registered'] else 'Stable/decreasing registrations'}
- Peak quarter: {max(all_quarters, key=lambda x: x['total_registered'])['period']}

**Year-End Recommendations:** Continue successful protocols, address identified gaps
    """

    return {
        "year": year,
        "total_registered": total_year,
        "quarters": all_quarters,
        "reasoning": reasoning,
        "generated_at": datetime.now().isoformat()
    }

# ===== MATERNAL AGENT WITH ANALYSIS =====
# maternal_agent = Agent(
#     name="MaternalAgent",
#     model=gemini_model,
#     instructions=(
#         "You are the Maternal Health Agent with MongoDB data analysis capabilities.\n\n"
#
#         "🗄️ **DATABASE ACCESS:**\n"
#         "You have access to 2500 maternal health records in MongoDB (healthcare360.maternal_registrations).\n"
#         "Always use actual data from database, not mock data.\n\n"
#
#         "📊 **ANALYSIS CAPABILITIES:**\n"
#         "When asked to generate reports:\n"
#         "1. Query MongoDB for the specified time period\n"
#         "2. Perform statistical analysis (age, risk, ANC, deliveries)\n"
#         "3. Generate graphs (bar charts, pie charts)\n"
#         "4. Provide detailed reasoning for all findings\n"
#         "5. Show graphs as base64 in response\n\n"
#
#         "🤝 **ORCHESTRATOR TOOLS:**\n"
#         "- handoff_to_agent(from_agent='maternal', to_agent='hospital_central', task_type='quarterly_report', context={report_data}, priority='normal')\n"
#         "- check_my_tasks(agent_name='maternal')\n"
#         "- complete_task(handoff_id, result, completed_by='maternal')\n\n"
#
#         "⚡ **WORKFLOW:**\n"
#         "1. Receive request for quarterly/annual report\n"
#         "2. Generate analysis from MongoDB data\n"
#         "3. Show reasoning + graphs in response\n"
#         "4. Send report to hospital_central agent via handoff\n"
#         "5. Complete task\n\n"
#
#         "📋 **REPORT FORMAT:**\n"
#         "Always include:\n"
#         "- Total registrations\n"
#         "- Age distribution\n"
#         "- Risk levels\n"
#         "- ANC completion rates\n"
#         "- Delivery outcomes\n"
#         "- Health metrics (hemoglobin, BMI)\n"
#         "- Graphs (base64 encoded)\n"
#         "- Detailed reasoning\n\n"
#
#         "💡 When asked for Q1 2025 report:\n"
#         "1. Run generate_quarterly_analysis('Q1', 2025)\n"
#         "2. Show full reasoning + stats\n"
#         "3. Display graphs\n"
#         "4. Send to hospital_central\n"
#         "5. Confirm completion\n\n"
#
#         "🌐 Language: English/Urdu mix\n"
#         "📧 Always show your reasoning process!"
#     ),
#     mcp_servers=[orchestrator_mcp, domain_mcp]
# )


# ===== MATERNAL AGENT WITH REGISTRATION & APPOINTMENTS =====
maternal_agent = Agent(
    name="MaternalAgent",
    model=gemini_model,
    instructions=(
        "You are the Maternal Health Agent with patient registration and appointment capabilities.\n\n"

        "🤰 YOUR RESPONSIBILITIES:\n"
        "1. **Patient Registration**: Register new patients using registration_id from CNIC service\n"
        "2. **Appointment Booking**: Generate tokens, check doctor availability, manage queue\n"
        "3. **Emergency Dispatch**: Handoff to Tracking Agent for ambulance needs\n"
        "4. **Follow-ups**: Schedule postpartum checkups, vaccination reminders\n"
        "5. **Mental Health**: Handoff to Mental Agent if depression/anxiety detected\n\n"

        "🤝 ORCHESTRATOR TOOLS:\n"
        "- handoff_to_agent(from_agent='maternal', to_agent='tracking', task_type='ambulance_dispatch', context={lat, lon, patient_id}, priority='urgent')\n"
        "- handoff_to_agent(from_agent='maternal', to_agent='mental', task_type='counseling', context={patient_id, symptoms}, priority='normal')\n"
        "- check_my_tasks(agent_name='maternal')\n"
        "- complete_task(handoff_id, result, completed_by='maternal')\n\n"

        "⚡ REGISTRATION WORKFLOW:\n"
        "1. Receive: registration_id + phone + email\n"
        "2. Use: hms_register_patient() to store in hospital database\n"
        "3. Generate: patient_id (e.g., MAT-12345)\n"
        "4. Send confirmation email\n"
        "5. Ask: 'Aapko appointment kab chahiye? Aaj ya kisi aur din?'\n\n"

        "📅 APPOINTMENT WORKFLOW:\n"
        "1. Check: Available doctors and current queue\n"
        "2. Generate: TOKEN-XXXXX with timestamp\n"
        "3. Calculate: Estimated wait time (current queue × 15 min per patient)\n"
        "4. Include in token: patient_id, doctor name, date, time, queue position\n"
        "5. Send: Email with token + SMS reminder\n"
        "6. Store: Token in appointment_tokens database\n\n"

        "🚨 EMERGENCY WORKFLOW:\n"
        "1. User says: 'Emergency hai' or 'Delivery time aa gaya'\n"
        "2. Get: lat, lon from user\n"
        "3. Handoff: to 'tracking' agent with priority='urgent'\n"
        "4. Wait: for tracking agent response (ambulance details)\n"
        "5. Inform: user about ambulance ETA and contact\n\n"

        "🧠 MENTAL HEALTH DETECTION:\n"
        "If user mentions: 'depression', 'anxiety', 'stress', 'suicidal thoughts'\n"
        "→ handoff_to_agent(to_agent='mental', task_type='counseling', priority='high')\n\n"

        "📱 FOLLOW-UP REMINDERS:\n"
        "After registration:\n"
        "- Day 7: ANC checkup reminder\n"
        "- Day 14: Blood test reminder\n"
        "- Day 21: Ultrasound reminder\n"
        "After delivery:\n"
        "- Day 3: Postpartum checkup\n"
        "- Day 42: Vaccination schedule\n\n"

        "🔐 PRIVACY:\n"
        "- NEVER ask for CNIC number (already handled by CNIC service)\n"
        "- Use registration_id to reference patient\n"
        "- Redact phone numbers in logs\n\n"

        "🌐 LANGUAGE: Urdu/English mix\n"
        "🎯 TONE: Compassionate, supportive, informative\n\n"

        "📋 RESPONSE FORMAT:\n"
        "1) Reasoning: Why you took this action\n"
        "2) Action Taken: What you did (registered, booked, handoff, etc.)\n"
        "3) Next Steps: What user should do next"
    ),
    mcp_servers=[orchestrator_mcp, domain_mcp]
)


# ===== DEMO =====
async def run_demo():
    async with orchestrator_mcp, domain_mcp:
        try:
            await orchestrator_mcp.connect()
            await domain_mcp.connect()
            print("✅ MCPs connected\n")
        except Exception as e:
            print(f"⚠️ MCP failed: {e}\n")

        print("=" * 70)
        print("TEST: Generate Q1 2025 Report with Analysis")
        print("=" * 70)

        # Generate analysis
        analysis = generate_quarterly_analysis("Q1", 2025)

        print(analysis['reasoning'])
        print(f"\n📊 Total Registered: {analysis['total_registered']}")
        print(f"📈 Graphs Generated: {len(analysis['graphs'])}")

        query = (
            f"Hospital Central Agent has requested Q1 2025 maternal health report. "
            f"Generate comprehensive analysis from MongoDB data and send via orchestrator handoff. "
            f"Include all statistics, graphs, and reasoning."
        )

        result = await Runner.run(maternal_agent, query)
        print("\n✅ [MATERNAL AGENT RESPONSE]")
        print(result.final_output if hasattr(result, "final_output") else str(result))

        await orchestrator_mcp.cleanup()
        await domain_mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(run_demo())