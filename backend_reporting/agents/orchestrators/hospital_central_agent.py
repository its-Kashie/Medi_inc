# hospital_central_agent.py - Hospital Central Agent (8 Departments Aggregation)
import asyncio
import json
import os
import time
from datetime import datetime
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
GEMINI_API_KEY = 'AIzaSyA3zCrC4YUAiy5Ct-hwVFfDSCd-l5l1KJM'

# if not GEMINI_API_KEY:
#     raise ValueError("❌ GEMINI_API_KEY not found in .env file!")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# ===== MCP SERVERS =====
# Use unified agents_mcp (NOT nih_mcp_server)
agents_mcp = MCPServerStdio(
    params={"command": "python", "args": [os.path.join(BASE_DIR, "mcp_servers/core_agents_mcp/agents_mcp.py")]},
    cache_tools_list=True,
    name="UnifiedMCP"
)

orchestrator_mcp = MCPServerStdio(
    params={"command": "python", "args": [os.path.join(BASE_DIR, "mcp_servers/orchestrator_mcp/agent_orchestrator_mcp.py")]},
    cache_tools_list=True,
    name="OrchestratorMCP"
)

# ===== HOSPITAL CENTRAL AGENT (8 DEPARTMENTS) =====
hospital_central_agent = Agent(
    name="HospitalCentralAgent",
    model=gemini_model,
    instructions=(
        """
You are the Hospital Central Agent for Services Hospital Lahore.
Your job is very simple:

1. NIH will ask you to submit Q1 2025 reports for all 8 departments.
2. You will start the batch report generation using the NEW tool:
   start_all_departments_batch(hospital="Services Hospital Lahore", quarter=1, year=2025)

3. It will return a batch_id immediately.
4. You will then check progress every 20 seconds using:
   get_batch_status(batch_id)

5. When status becomes "completed", you will see all 8 reports are ready.
6. Then you will calculate total patients from the completed reports.
7. Finally, handoff to NIH using:
   handoff_to_agent('hospital_central', 'nih', 'report_submission', {
       'hospital': 'Services Hospital Lahore',
       'quarter': 'Q1',
       'year': 2025,
       'batch_id': batch_id,
       'total_departments': 8,
       'total_patients': <sum>,
       'status': 'all_reports_ready'
   }, 'high')

DO NOT use any old tool names like generate_cardiology_report_full
DO NOT wait for signatures
DO NOT aggregate manually
Just use the two new tools: start_all_departments_batch and get_batch_status
"""
    ),
    mcp_servers=[agents_mcp, orchestrator_mcp]
)
apply_key_to_agent("hospital_central", hospital_central_agent)

# ===== DEMO =====
async def run_full_hospital_demo():
    """Demo: Hospital Central receives NIH request and aggregates 8 departments"""

    async with agents_mcp, orchestrator_mcp:
        await agents_mcp.connect()
        await orchestrator_mcp.connect()

        print("=" * 80)
        print("HOSPITAL CENTRAL AGENT - 8 DEPARTMENTS AGGREGATION")
        print("=" * 80)

        query = (
            "NIH has sent you a request: 'Submit Q1 2025 quarterly reports for ALL 8 departments from Services Hospital Lahore.'\n\n"
            "Execute the complete workflow:\n"
            "1. Generate reports for all 8 departments using the report generation tools\n"
            "2. Wait for focal person signatures (10 seconds per department)\n"
            "3. Aggregate all 8 reports using aggregate_all_departments_national()\n"
            "4. Submit aggregated report to NIH using handoff_to_agent()\n"
            "5. Show complete reasoning for each step"
        )

        result = await Runner.run(hospital_central_agent, query, max_turns=30)
        print("\n✅ Hospital Central Response:")
        print(result.final_output)

        await agents_mcp.cleanup()
        await orchestrator_mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(run_full_hospital_demo())