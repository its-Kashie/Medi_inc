# nih_agent.py - FIXED: Enhanced NIH Agent with WHO Proposal Generation
"""
NIH Agent responsibilities:
1. Send quarterly report requests to all 10 hospitals
2. Receive reports from Hospital Central Agents (8 departments each)
3. Validate report completeness
4. Aggregate national data by department (8 national reports)
5. Identify research priorities
6. Generate WHO proposals ← FIXED: Now has rnd_mcp tools
7. Send aggregated data to R&D Agent
8. Display national dashboard
"""
import os
import asyncio
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

# ===== ADD THIS NEW LINE =====
from agent_key_manager import apply_key_to_agent   # ← yehi line daal do
# ===== LOAD ENV =====
from dotenv import load_dotenv
load_dotenv()

# ===== GEMINI SETUP =====
GEMINI_API_KEY = 'AIzaSyBJ3zGrLZ-czuUq8_a3ZyGuZLAWus1w8AQ'


client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# ===== MCP SERVERS =====
# Core hospital_agents MCP
agents_mcp = MCPServerStdio(
    params={"command": "python", "args": [os.path.join(BASE_DIR, "mcp_servers/core_agents_mcp/agents_mcp.py")]},
    cache_tools_list=True,
    name="CoreAgentsMCP"
)

# NIH MCP (national aggregation)
nih_mcp = MCPServerStdio(
    params={"command": "python", "args": [os.path.join(BASE_DIR, "mcp_servers/nih_mcp/nih_mcp.py")]},
    cache_tools_list=True,
    name="NIH_MCP"
)

# Orchestrator for inter-agent communication
orchestrator_mcp = MCPServerStdio(
    params={"command": "python", "args": [os.path.join(BASE_DIR, "mcp_servers/orchestrator_mcp/agent_orchestrator_mcp.py")]},
    cache_tools_list=True,
    name="OrchestratorMCP"
)

# ===== CRITICAL FIX: Add R&D MCP for WHO Proposal Generation =====
rnd_mcp = MCPServerStdio(
    params={"command": "python", "args": [os.path.join(BASE_DIR, "mcp_servers/rnd_mcp/rnd_mcp_tools.py")]},
    cache_tools_list=True,
    name="RND_MCP"
)

# ===== ENHANCED NIH AGENT (FIXED) =====
nih_agent = Agent(
    name="NIHAgent_Enhanced",
    model=gemini_model,
    instructions=(
        "🏛️ **NATIONAL INSTITUTE OF HEALTH (NIH) AGENT - ENHANCED**\n\n"

        "**Mission:** National healthcare intelligence, data aggregation, and WHO proposal generation.\n\n"

        "**Your Responsibilities:**\n"
        "1. **Request Reports** from 10 hospitals (quarterly reminders)\n"
        "2. **Receive & Validate** 80 department reports (10 hospitals × 8 departments)\n"
        "3. **Aggregate National Data** by department → 8 national reports\n"
        "4. **Identify Research Priorities** based on national trends\n"
        "5. **Generate WHO Proposals** (Word documents with graphs) ← YOUR JOB!\n"
        "6. **Send Data to R&D Agent** for university email distribution\n"
        "7. **Display National Dashboard** with key metrics\n\n"

        "**🛠️ AVAILABLE TOOLS:**\n\n"

        "**National Aggregation (from nih_mcp.py):**\n"
        "- `aggregate_all_departments_national(quarter, year)` → Get ALL 8 departments, all hospitals\n"
        "  Returns: Complete national dataset with department_breakdown\n\n"

        "- `aggregate_national_statistics(department, quarter, year)` → Single department, all hospitals\n"
        "  Returns: total_cases_national, hospitals_reporting, mortality_rate, etc.\n\n"

        "- `analyze_three_year_trends(department, hospital)` → 3-year historical data (2023-2025)\n"
        "  Returns: quarterly_breakdown, total_patients_3yr, trend_direction\n\n"

        "- `get_report_statistics(hospital, quarter, year)` → Quick stats for 1 hospital\n\n"

        "**Research Priorities (from rnd_mcp_tools.py):**\n"
        "- `identify_research_priorities(national_data_all_depts)` → Analyze all 8 departments\n"
        "  Returns: high_priority, medium_priority, low_priority lists with justifications\n\n"

        "**WHO PROPOSAL GENERATION (from rnd_mcp_tools.py) - CRITICAL:**\n"
        "- `generate_who_funding_proposal_docx(research_area, national_data_summary, three_year_trends, priority_justification)` → Generate Word document\n"
        "  Args:\n"
        "    - research_area: e.g., 'Maternal Health Crisis in Pakistan'\n"
        "    - national_data_summary: Dict from aggregate_all_departments_national() or aggregate_national_statistics()\n"
        "    - three_year_trends: Dict from analyze_three_year_trends()\n"
        "    - priority_justification: Why urgent (cite specific numbers)\n"
        "  Returns:\n"
        "    - status: 'success'\n"
        "    - file_path: 'generated_reports/who_proposals/WHO_Proposal_....docx'\n"
        "    - filename: 'WHO_Proposal_Maternal_Health_20250120.docx'\n"
        "    - download_url: '/api/proposals/download?file=...'\n"
        "    - file_size_mb: 2.3\n"
        "  Output: Professional 15-page Word document with:\n"
        "    - Title page\n"
        "    - Executive summary\n"
        "    - Disease burden analysis\n"
        "    - 3-year trend graphs (PNG images embedded)\n"
        "    - Funding request ($500K USD)\n"
        "    - Intervention plan\n"
        "    - Expected outcomes\n"
        "    - Implementation partners\n"
        "    - Sustainability plan\n"
        "    - Signatures section\n\n"

        "**Inter-Agent Communication (from orchestrator):**\n"
        "- `check_my_tasks('nih')` → Check incoming messages\n"
        "- `handoff_to_agent('nih', 'hospital_central', 'report_request', {...}, 'normal')` → Request reports\n"
        "- `handoff_to_agent('nih', 'rnd', 'national_data_ready', {...}, 'high')` → Send to R&D\n"
        "- `complete_task(handoff_id, result, 'nih')` → Mark tasks complete\n\n"

        "**📊 10 HOSPITALS TO MONITOR:**\n"
        "1. Mayo Hospital\n"
        "2. Services Hospital Lahore\n"
        "3. Jinnah Hospital Lahore\n"
        "4. Sir Ganga Ram Hospital\n"
        "5. Shalamar Hospital\n"
        "6. Lady Willingdon Hospital\n"
        "7. Fatima Memorial Hospital\n"
        "8. Shaukat Khanum Memorial\n"
        "9. PKLI Lahore\n"
        "10. Bahria International\n\n"

        "**📋 8 DEPARTMENTS TO TRACK:**\n"
        "1. **Infectious Diseases** → Research area: 'Water-borne Disease Crisis'\n"
        "2. **Maternal Health** → Research area: 'Maternal Health Crisis: C-Section Epidemic'\n"
        "3. **Nutrition** → Research area: 'Child Malnutrition in Pakistan'\n"
        "4. **Mental Health** → Research area: 'Mental Health Crisis: Rising Depression Rates'\n"
        "5. **NCD (Internal Medicine)** → Research area: 'Non-Communicable Diseases Burden'\n"
        "6. **Cardiology** → Research area: 'Cardiovascular Disease Prevention'\n"
        "7. **Endocrinology** → Research area: 'Diabetes Management Crisis'\n"
        "8. **Oncology** → Research area: 'Cancer Early Detection Programs'\n\n"

        "**🔄 COMPLETE WORKFLOW WITH WHO PROPOSALS:**\n\n"

        "**PHASE 1: Send Quarterly Reminders**\n"
        "```\n"
        "1. handoff_to_agent('nih', 'hospital_central', 'report_request', {...})\n"
        "2. Log: 'Reminders sent to 10 hospitals'\n"
        "```\n\n"

        "**PHASE 2: Receive & Validate Reports**\n"
        "```\n"
        "1. check_my_tasks('nih')\n"
        "2. Track: 80 total reports expected\n"
        "```\n\n"

        "**PHASE 3: Aggregate National Data**\n"
        "```\n"
        "1. national_data = aggregate_all_departments_national('Q1', 2025)\n"
        "2. Result shows:\n"
        "   - total_patients_all_departments: 28,450\n"
        "   - total_hospitals: 10\n"
        "   - department_breakdown: {8 departments with stats}\n"
        "```\n\n"

        "**PHASE 4: Identify Top 3 Research Priorities**\n"
        "```\n"
        "1. priorities = identify_research_priorities(national_data)\n"
        "2. Extract high_priority list (top 3)\n"
        "3. Example output:\n"
        "   high_priority: [\n"
        "     {'department': 'Maternal Health', 'total_cases': 12500, 'justification': '45% C-section rate'},\n"
        "     {'department': 'Infectious Diseases', 'total_cases': 8200, 'justification': 'Cholera outbreak'},\n"
        "     {'department': 'Mental Health', 'total_cases': 3100, 'justification': '8% suicide risk'}\n"
        "   ]\n"
        "```\n\n"

        "**PHASE 5: Generate 3 WHO Proposals (CRITICAL - YOUR MAIN JOB!)**\n"
        "```\n"
        "For EACH of the top 3 priorities:\n\n"

        "1. Get 3-year trends:\n"
        "   maternal_trends = analyze_three_year_trends('Maternal Health', 'Mayo Hospital')\n\n"

        "2. Get national statistics:\n"
        "   maternal_data = aggregate_national_statistics('Maternal Health', 'Q1', 2025)\n\n"

        "3. Generate WHO proposal (Word document):\n"
        "   proposal_1 = generate_who_funding_proposal_docx(\n"
        "     research_area='Maternal Health Crisis: C-Section Epidemic in Urban Pakistan',\n"
        "     national_data_summary=maternal_data,\n"
        "     three_year_trends=maternal_trends,\n"
        "     priority_justification='National C-section rate is 45%, triple the WHO recommendation of 15%. Analysis of 12,500 maternal cases across 10 hospitals shows urgent intervention needed.'\n"
        "   )\n"
        "   # Returns: {'status': 'success', 'file_path': '...', 'filename': 'WHO_Proposal_Maternal_Health_20250120.docx'}\n\n"

        "4. Repeat for Infectious Diseases:\n"
        "   infectious_trends = analyze_three_year_trends('Infectious Diseases', 'Mayo Hospital')\n"
        "   infectious_data = aggregate_national_statistics('Infectious Diseases', 'Q1', 2025)\n"
        "   proposal_2 = generate_who_funding_proposal_docx(\n"
        "     research_area='Water-borne Disease Crisis: Cholera Outbreak in Pakistan',\n"
        "     national_data_summary=infectious_data,\n"
        "     three_year_trends=infectious_trends,\n"
        "     priority_justification='8,200 cases with 6.1% mortality rate. Cholera outbreak detected in 3 districts.'\n"
        "   )\n\n"

        "5. Repeat for Mental Health:\n"
        "   mental_trends = analyze_three_year_trends('Mental Health', 'Mayo Hospital')\n"
        "   mental_data = aggregate_national_statistics('Mental Health', 'Q1', 2025)\n"
        "   proposal_3 = generate_who_funding_proposal_docx(\n"
        "     research_area='Mental Health Crisis: Rising Depression and Suicide Risk',\n"
        "     national_data_summary=mental_data,\n"
        "     three_year_trends=mental_trends,\n"
        "     priority_justification='3,100 cases with 8% flagged as high suicide risk. 35% increase in depression diagnoses since 2023.'\n"
        "   )\n\n"

        "6. Display results:\n"
        "   ✅ WHO Proposal 1: WHO_Proposal_Maternal_Health_20250120.docx (2.3 MB)\n"
        "   ✅ WHO Proposal 2: WHO_Proposal_Infectious_Diseases_20250120.docx (2.1 MB)\n"
        "   ✅ WHO Proposal 3: WHO_Proposal_Mental_Health_20250120.docx (1.9 MB)\n"
        "```\n\n"

        "**PHASE 6: Send to R&D Agent**\n"
        "```\n"
        "1. handoff_to_agent('nih', 'rnd', 'national_data_ready', {\n"
        "     'national_data': national_data,\n"
        "     'priorities': priorities,\n"
        "     'who_proposals': [\n"
        "       {'file': proposal_1['filename'], 'area': 'Maternal Health'},\n"
        "       {'file': proposal_2['filename'], 'area': 'Infectious Diseases'},\n"
        "       {'file': proposal_3['filename'], 'area': 'Mental Health'}\n"
        "     ],\n"
        "     'quarter': 'Q1',\n"
        "     'year': 2025\n"
        "   }, 'high')\n"
        "```\n\n"

        "**💡 REASONING FORMAT:**\n"
        "Always explain:\n"
        "1. **Data Aggregation:** Total cases per department\n"
        "2. **Priority Analysis:** Why top 3 selected (cite numbers)\n"
        "3. **3-Year Trends:** Increasing/decreasing patterns\n"
        "4. **WHO Proposals:** Which Word documents generated (show file paths)\n"
        "5. **R&D Handoff:** What sent to R&D Agent\n\n"

        "**🎯 SUCCESS CRITERIA:**\n"
        "- ✅ National data aggregated (all 8 departments)\n"
        "- ✅ Top 3 priorities identified with evidence\n"
        "- ✅ 3 WHO proposals generated (Word documents)\n"
        "- ✅ File paths and download URLs provided\n"
        "- ✅ Data package sent to R&D Agent\n\n"

        "**🚨 CRITICAL RULES:**\n"
        "1. **WHO proposals = Word documents** - Not JSON, not text summaries!\n"
        "2. **Use generate_who_funding_proposal_docx()** - This is in rnd_mcp_tools.py\n"
        "3. **Include 3-year trends** - Makes proposals more compelling\n"
        "4. **Cite specific numbers** - Mortality rates, case volumes\n"
        "5. **Generate exactly 3 proposals** - For top 3 priorities only\n"
        "6. **Show file paths** - Confirm files_should_be_in_1_directory were created\n\n"

        "**Example Complete Response:**\n"
        "```\n"
        "🏛️ NIH AGENT - Q1 2025 NATIONAL ANALYSIS\n\n"

        "**Step 1: National Data Aggregated**\n"
        "- Total patients: 28,450 across 10 hospitals\n"
        "- 8 departments analyzed\n\n"

        "**Step 2: Top 3 Research Priorities Identified**\n"
        "1. Maternal Health: 12,500 cases, 45% C-section rate (WHO rec: 15%)\n"
        "2. Infectious Diseases: 8,200 cases, 6.1% mortality, cholera outbreak\n"
        "3. Mental Health: 3,100 cases, 8% high suicide risk\n\n"

        "**Step 3: 3-Year Trends Analyzed**\n"
        "- Maternal: C-sections increased 12% (2023-2025)\n"
        "- Infectious: Cholera cases up 22% in 2024\n"
        "- Mental: Depression diagnoses up 35%\n\n"

        "**Step 4: WHO Proposals Generated (Word Documents)**\n"
        "✅ Proposal 1: WHO_Proposal_Maternal_Health_20250120.docx\n"
        "   - File size: 2.3 MB\n"
        "   - Download: /api/proposals/download?file=WHO_Proposal_Maternal_Health_20250120.docx\n"
        "   - Funding: $500,000 USD\n"
        "   - 15 pages with 3-year trend graphs\n\n"

        "✅ Proposal 2: WHO_Proposal_Infectious_Diseases_20250120.docx\n"
        "   - File size: 2.1 MB\n"
        "   - Funding: $500,000 USD\n\n"

        "✅ Proposal 3: WHO_Proposal_Mental_Health_20250120.docx\n"
        "   - File size: 1.9 MB\n"
        "   - Funding: $500,000 USD\n\n"

        "**Step 5: Sent to R&D Agent**\n"
        "Data package handed off to R&D for university distribution.\n"
        "R&D will send emails to 38 universities with proposals attached.\n"
        "```\n\n"

        "**🌐 Language:** English\n"
        "**📍 Context:** Pakistan healthcare system\n"
    ),
    mcp_servers=[agents_mcp, nih_mcp, orchestrator_mcp, rnd_mcp]  # ← FIXED: Added rnd_mcp!
)

apply_key_to_agent("nih", nih_agent)
# ===== DEMO FUNCTIONS (keep existing ones, add new WHO proposal demo) =====

async def demo_nih_who_proposals_word_docs():
    """Demo: NIH generates WHO proposals as Word documents (FIXED)"""

    async with agents_mcp, nih_mcp, orchestrator_mcp, rnd_mcp:
        await agents_mcp.connect()
        await nih_mcp.connect()
        await orchestrator_mcp.connect()
        await rnd_mcp.connect()

        print("\n" + "=" * 80)
        print("NIH AGENT - WHO PROPOSAL GENERATION (WORD DOCUMENTS)")
        print("=" * 80)

        query = (
            "🏛️ NIH AGENT - GENERATE WHO FUNDING PROPOSALS\n\n"

            "**Step 1: Get National Data**\n"
            "Call aggregate_all_departments_national('Q1', 2025) to get complete national statistics.\n\n"

            "**Step 2: Identify Top 3 Priorities**\n"
            "Call identify_research_priorities(national_data) to get high-priority list.\n\n"

            "**Step 3: For EACH Top 3 Priority, Generate WHO Proposal:**\n"
            "Example for Maternal Health:\n"
            "  1. Get trends: analyze_three_year_trends('Maternal Health', 'Mayo Hospital')\n"
            "  2. Get data: aggregate_national_statistics('Maternal Health', 'Q1', 2025)\n"
            "  3. Generate proposal:\n"
            "     generate_who_funding_proposal_docx(\n"
            "       research_area='Maternal Health Crisis in Pakistan',\n"
            "       national_data_summary=maternal_data,\n"
            "       three_year_trends=maternal_trends,\n"
            "       priority_justification='45% C-section rate, 12,500 cases analyzed'\n"
            "     )\n\n"

            "Repeat this process for ALL 3 high-priority areas.\n\n"

            "**Step 4: Display Results**\n"
            "Show:\n"
            "- File paths for all 3 Word documents\n"
            "- File sizes\n"
            "- Download URLs\n"
            "- Research areas covered\n\n"

            "**CRITICAL:** You MUST actually CALL generate_who_funding_proposal_docx() for each priority!\n"
            "Don't just plan to do it - DO IT NOW!"
        )

        result = await Runner.run(nih_agent, query, max_turns=40)
        print("\n✅ WHO Proposals Generated:")
        print(result.final_output)

        await agents_mcp.cleanup()
        await nih_mcp.cleanup()
        await orchestrator_mcp.cleanup()
        await rnd_mcp.cleanup()


async def demo_nih_complete_workflow():
    """Demo: Complete NIH workflow including WHO proposals"""

    async with agents_mcp, nih_mcp, orchestrator_mcp, rnd_mcp:
        await agents_mcp.connect()
        await nih_mcp.connect()
        await orchestrator_mcp.connect()
        await rnd_mcp.connect()

        print("\n" + "=" * 80)
        print("NIH AGENT - COMPLETE QUARTERLY WORKFLOW WITH WHO PROPOSALS")
        print("=" * 80)

        query = (
            "Execute the COMPLETE NIH quarterly workflow for Q1 2025:\n\n"

            "PHASE 1: Aggregate national data for ALL 8 departments\n"
            "  - Use aggregate_all_departments_national('Q1', 2025)\n\n"

            "PHASE 2: Identify top 3 research priorities\n"
            "  - Use identify_research_priorities(national_data)\n\n"

            "PHASE 3: Generate 3 WHO proposals (Word documents)\n"
            "  - For EACH top priority:\n"
            "    1. Get 3-year trends\n"
            "    2. Get national statistics\n"
            "    3. Call generate_who_funding_proposal_docx()\n"
            "  - Show file paths and download URLs\n\n"

            "PHASE 4: Send data package to R&D Agent\n"
            "  - Use handoff_to_agent('nih', 'rnd', 'national_data_ready', {...}, 'high')\n\n"

            "Show detailed progress for EACH phase with file paths."
        )

        result = await Runner.run(nih_agent, query, max_turns=50)
        print("\n✅ Complete Workflow Result:")
        print(result.final_output)

        await agents_mcp.cleanup()
        await nih_mcp.cleanup()
        await orchestrator_mcp.cleanup()
        await rnd_mcp.cleanup()


async def demo_nih_generate_who_proposals_standalone():
    """
    Standalone demo: NIH generates 3 WHO proposals (Word documents)
    No workflow needed - just generates proposals directly
    """

    async with agents_mcp, nih_mcp, orchestrator_mcp, rnd_mcp:
        await agents_mcp.connect()
        await nih_mcp.connect()
        await orchestrator_mcp.connect()
        await rnd_mcp.connect()

        print("\n" + "=" * 80)
        print("🏛️ NIH AGENT - STANDALONE WHO PROPOSAL GENERATION")
        print("=" * 80)
        print("\n📋 This will generate 3 WHO funding proposals as Word documents")
        print("⏱️  Expected time: 3-5 minutes\n")

        query = (
            "🏛️ NIH AGENT - GENERATE 3 WHO FUNDING PROPOSALS\n\n"

            "**Your Mission:**\n"
            "Generate 3 professional WHO funding proposals (Word documents) for Q1 2025.\n\n"

            "**PHASE 1: Get National Data**\n"
            "Call aggregate_all_departments_national('Q1', 2025) to get complete statistics.\n\n"

            "**PHASE 2: Identify Top 3 Priorities**\n"
            "Call identify_research_priorities(national_data).\n"
            "Select the 3 highest-priority areas based on:\n"
            "- Mortality rates\n"
            "- Case volumes  \n"
            "- Trend severity\n\n"

            "**PHASE 3: Generate WHO Proposals (CRITICAL - DO ALL 3!)**\n"
            "For EACH of the top 3 priorities:\n\n"

            "Example for Priority #1 (Maternal Health):\n"
            "```\n"
            "1. Get 3-year trends:\n"
            "   maternal_trends = analyze_three_year_trends('Maternal Health', 'Mayo Hospital')\n\n"

            "2. Get national statistics:\n"
            "   maternal_data = aggregate_national_statistics('Maternal Health', 'Q1', 2025)\n\n"

            "3. Generate Word document:\n"
            "   proposal_1 = generate_who_funding_proposal_docx(\n"
            "     research_area='Maternal Health Crisis: High C-Section Rates in Pakistan',\n"
            "     national_data_summary=maternal_data,\n"
            "     three_year_trends=maternal_trends,\n"
            "     priority_justification='National C-section rate is 45% (WHO recommends 15%). Analysis of 12,500 cases shows urgent need.'\n"
            "   )\n"
            "```\n\n"

            "Repeat this exact process for Priority #2 and Priority #3.\n\n"

            "**PHASE 4: Display Results**\n"
            "Show for each proposal:\n"
            "- ✅ Proposal filename (e.g., WHO_Proposal_Maternal_Health_20250120.docx)\n"
            "- 📁 File path\n"
            "- 📊 File size (MB)\n"
            "- 🔗 Download URL\n"
            "- 💰 Funding amount ($500,000 USD)\n"
            "- 📈 Research area\n\n"

            "**CRITICAL RULES:**\n"
            "1. You MUST call generate_who_funding_proposal_docx() exactly 3 times\n"
            "2. Each call generates a complete 15-page Word document\n"
            "3. Include 3-year trend graphs in each proposal\n"
            "4. Cite specific national data (mortality rates, case volumes)\n"
            "5. Show file paths to confirm documents were created\n\n"

            "**DO NOT just plan - ACTUALLY GENERATE THE 3 DOCUMENTS NOW!**"
        )

        print("🚀 Starting WHO proposal generation...\n")

        try:
            result = await Runner.run(nih_agent, query, max_turns=40)

            print("\n" + "=" * 80)
            print("✅ WHO PROPOSALS GENERATED - RESULTS:")
            print("=" * 80)
            print(result.final_output)
            print("\n" + "=" * 80)
            print("📂 Check folder: generated_reports/who_proposals/")
            print("🌐 Download via: http://localhost:8000/api/proposals/download?file=[filename]")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Error during proposal generation: {e}")

        await agents_mcp.cleanup()
        await nih_mcp.cleanup()
        await orchestrator_mcp.cleanup()
        await rnd_mcp.cleanup()

# ===== CLI INTERFACE (UPDATED) =====

async def main():
    """Main CLI interface for NIH Agent"""
    import sys

    if len(sys.argv) < 2:
        print("\n🏛️ NIH Agent - Command Interface (FIXED)")
        print("=" * 80)
        print("\nUsage:")
        print("  python nih_agent.py aggregate    - Aggregate national data")
        print("  python nih_agent.py priorities   - Identify research priorities")
        print("  python nih_agent.py proposals    - Generate 3 WHO proposals (Word docs) ← FIXED!")
        print("  python nih_agent.py complete     - Execute complete workflow with WHO proposals")
        print("\nExamples:")
        print("  python nih_agent.py proposals    # Generate WHO Word documents")
        print("  python nih_agent.py complete     # Full workflow with proposals")
        return

    command = sys.argv[1].lower()

    if command == "aggregate":
        await demo_nih_aggregate_national()
    elif command == "priorities":
        await demo_nih_research_priorities()
    elif command == "proposals":
        await demo_nih_who_proposals_word_docs()  # ← NEW FIXED VERSION
    elif command == "complete":
        await demo_nih_complete_workflow()  # ← UPDATED VERSION
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see usage")

if __name__ == "__main__":
    asyncio.run(main())