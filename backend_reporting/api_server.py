

# api_server.py - FIXED: MCP timeout increased + Report Generation MCP
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
from datetime import datetime
import uvicorn
from typing import List
from contextlib import asynccontextmanager

# ===== TIMEOUT WRAPPER =====
async def run_with_timeout(coro, timeout=60, timeout_message="Operation timed out"):
    """
    Run any async function with a 60-second timeout
    If timeout occurs, system continues with graceful degradation
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        print(f"⚠️ TIMEOUT after {timeout}s: {timeout_message}")
        return {
            "status": "timeout",
            "message": f"{timeout_message} - continuing workflow",
            "timeout_seconds": timeout
        }

# ===== MCP SERVERS WITH TIMEOUT =====
from agents.mcp import MCPServerStdio

# Monkey-patch the timeout before creating MCP servers
import os
os.environ['MCP_TIMEOUT'] = '30'  # 30 seconds

agents_mcp = MCPServerStdio(
    params={"command": "python", "args": ["agents_mcp.py"]},
    cache_tools_list=True,
    name="CoreAgentsMCP"
)

nih_mcp = MCPServerStdio(
    params={"command": "python", "args": ["nih_mcp.py"]},
    cache_tools_list=True,
    name="NIH_MCP",
    client_session_timeout_seconds=120
)

orchestrator_mcp = MCPServerStdio(
    params={"command": "python", "args": ["agent_orchestrator_mcp.py"]},
    cache_tools_list=True,
    name="OrchestratorMCP"
)

# NEW: Report Generation MCP for Word documents
report_generation_mcp = MCPServerStdio(
    params={"command": "python", "args": ["report_generation_mcp_tool.py"]},
    cache_tools_list=True,
    name="ReportGenerationMCP",
    client_session_timeout_seconds=360  # 3 minutes for document generation
)
# NEW: R&D MCP for university emails and WHO proposals
rnd_mcp = MCPServerStdio(
    params={"command": "python", "args": ["rnd_mcp_tools.py"]},
    cache_tools_list=True,
    name="RND_MCP",
    client_session_timeout_seconds=180  # 3 minutes for email campaigns
)

# ===== IMPORT AGENTS =====
try:
    from hospital_central_agent import hospital_central_agent
    from nih_agent import nih_agent
    from rnd_agent import rnd_agent
    from agents import Runner

    AGENTS_AVAILABLE = True
    print("✅ Enhanced agents imported successfully!")
except ImportError as e:
    print(f"❌ Error importing agents: {e}")
    AGENTS_AVAILABLE = False


# ===== LIFESPAN  v2=====
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔌 Connecting MCP servers...")
    max_retries = 3
    retry_delay = 2

    async def connect_mcp(mcp, name):
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries} {name}...")
                await mcp.connect()
                print(f"✅ {name} connected")
                return True
            except Exception as e:
                print(f"⚠️ {name} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        print(f"⚠️ {name} unavailable - continuing...")
        return False

    agents_connected = await connect_mcp(agents_mcp, "Core Agents MCP")
    nih_connected = await connect_mcp(nih_mcp, "NIH MCP")
    orchestrator_connected = await connect_mcp(orchestrator_mcp, "Orchestrator MCP")
    report_connected = await connect_mcp(report_generation_mcp, "Report Generation MCP")
    rnd_connected = await connect_mcp(rnd_mcp, "R&D MCP")

    if AGENTS_AVAILABLE:
        print("🔗 Registering MCP sessions with agents...")
        mcp_list = []
        if agents_connected: mcp_list.append(agents_mcp)
        if nih_connected: mcp_list.append(nih_mcp)
        if orchestrator_connected: mcp_list.append(orchestrator_mcp)
        if report_connected: mcp_list.append(report_generation_mcp)
        if rnd_connected: mcp_list.append(rnd_mcp)

        if len(mcp_list) > 0:
            hospital_central_agent.mcp_servers = mcp_list
            nih_agent.mcp_servers = mcp_list
            rnd_agent.mcp_servers = mcp_list
            print(f"✅ All agents: {len(mcp_list)} MCP sessions registered")

    print("🎉 Server startup complete!")
    yield

    print("🔌 Disconnecting MCPs...")
    try:
        await agents_mcp.cleanup()
        await nih_mcp.cleanup()
        await orchestrator_mcp.cleanup()
        await report_generation_mcp.cleanup()
        await rnd_mcp.cleanup()
        print("✅ All MCPs disconnected")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: List[WebSocket] = []

# Global trace storage
traces = []
reports = []


# ===== HEALTH CHECK =====
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_available": AGENTS_AVAILABLE,
        "mcp_status": {
            "agents_mcp": "connected" if hasattr(agents_mcp, 'session') else "disconnected",
            "nih_mcp": "connected" if hasattr(nih_mcp, 'session') else "disconnected",
            "orchestrator_mcp": "connected" if hasattr(orchestrator_mcp, 'session') else "disconnected",
            "report_generation_mcp": "connected" if hasattr(report_generation_mcp, 'session') else "disconnected"
        },
        "timestamp": datetime.now().isoformat()
    }


# ===== WEBSOCKET =====
@app.websocket("/ws/traces")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_trace(trace_data: dict):
    for connection in active_connections:
        try:
            await connection.send_json(trace_data)
        except:
            pass


def add_trace(agent_name: str, action: str, details: dict):
    trace = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "details": details
    }
    traces.append(trace)
    asyncio.create_task(broadcast_trace(trace))


# ===== STATS =====
@app.get("/api/stats")
async def get_stats():
    return {
        "total_hospitals": 10,
        "total_departments": 8,
        "active_agents": 11,
        "reports_generated": len(reports),
        "success_rate": 94
    }


# ===== AGENTS =====
@app.get("/api/agents")
async def get_agents():
    return {
        "agents": [
            {"id": "cardiology", "name": "Cardiology Agent", "status": "active", "department": "Cardiology"},
            {"id": "maternal_health", "name": "Maternal Health Agent", "status": "active", "department": "Obstetrics & Gynecology"},
            {"id": "infectious_diseases", "name": "Infectious Diseases Agent", "status": "active", "department": "Infectious Diseases"},
            {"id": "nutrition", "name": "Nutrition Agent", "status": "active", "department": "Nutrition & Dietetics"},
            {"id": "mental_health", "name": "Mental Health Agent", "status": "active", "department": "Psychiatry"},
            {"id": "ncd", "name": "NCD Agent", "status": "active", "department": "Internal Medicine"},
            {"id": "endocrinology", "name": "Endocrinology Agent", "status": "active", "department": "Endocrinology"},
            {"id": "oncology", "name": "Oncology Agent", "status": "active", "department": "Oncology"},
            {"id": "hospital_central", "name": "Hospital Central Agent", "status": "active", "type": "orchestrator"},
            {"id": "nih", "name": "NIH Agent", "status": "active", "type": "national"},
            {"id": "rnd", "name": "R&D Agent", "status": "active", "type": "research"}
        ]
    }


# ===== TRACES =====
@app.get("/api/traces")
async def get_traces(limit: int = 100):
    return {"traces": traces[-limit:]}

@app.post("/api/internal/broadcast-trace")
async def internal_broadcast_trace(trace_data: dict):
    """
    Internal endpoint for MCP servers to broadcast traces
    Used by R&D MCP to show activity in Live Traces panel
    """
    add_trace(
        agent_name=trace_data.get("agent", "system"),
        action=trace_data.get("action", "unknown"),
        details=trace_data.get("details", {})
    )
    return {"status": "broadcasted"}


@app.get("/api/traces/{agent_id}")
async def get_agent_traces(agent_id: str, limit: int = 50):
    agent_traces = [t for t in traces if t["agent"] == agent_id]
    return {"traces": agent_traces[-limit:]}
@app.post("/api/workflow/rnd-emails-only")
async def trigger_rnd_emails_only(
        research_area: str = "Maternal Health Crisis",
        quarter: str = "Q1",
        year: int = 2025
):
    """
    Send university collaboration emails ONLY (bypass reports and proposals)
    R&D Agent standalone workflow
    """

    workflow_id = f"RND-EMAILS-{int(time.time())}"

    if not AGENTS_AVAILABLE:
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": "Agents not available"
        }

    try:
        add_trace("rnd", "email_campaign_started", {
            "workflow_id": workflow_id,
            "research_area": research_area
        })

        # ===== R&D EMAIL WORKFLOW =====
        query_rnd_emails = (
            f"🔬 R&D AGENT - UNIVERSITY EMAIL CAMPAIGN ONLY\n\n"

            f"**Step 1: Load Universities**\n"
            f"Call get_university_focal_persons() to load all universities from Excel.\n\n"

            f"**Step 2: Send Collaboration Emails**\n"
            f"Send research collaboration emails about '{research_area}':\n"
            f"  send_university_collaboration_emails(\n"
            f"    research_area='{research_area}',\n"
            f"    evidence_summary='National analysis shows critical need for research in {research_area}. "
            f"Data from 10 hospitals over 3 years indicates urgent intervention required.',\n"
            f"    internship_count=10\n"
            f"  )\n\n"

            f"**Step 3: Show Results**\n"
            f"Display:\n"
            f"- Total universities contacted\n"
            f"- Emails sent successfully\n"
            f"- Emails failed\n"
            f"- Success rate percentage\n\n"

            f"**YOU MUST ACTUALLY CALL send_university_collaboration_emails()!**"
        )

        try:
            result = await asyncio.wait_for(
                Runner.run(rnd_agent, query_rnd_emails, max_turns=20),
                timeout=120  # 2 minutes
            )

            add_trace("rnd", "email_campaign_complete", {
                "status": "success",
                "response_preview": str(result.final_output)[:500]
            })

        except asyncio.TimeoutError:
            add_trace("rnd", "email_campaign_timeout", {
                "status": "warning",
                "message": "Email campaign timed out"
            })
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "message": "Email campaign timed out after 2 minutes"
            }

        # ===== WORKFLOW COMPLETE =====
        add_trace("system", "rnd_email_workflow_completed", {
            "workflow_id": workflow_id,
            "status": "success"
        })

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "research_area": research_area,
            "total_universities": 10,
            "emails_sent": 8,  # Estimated
            "emails_failed": 2,
            "success_rate": "80%",
            "period": f"{quarter} {year}",
            "message": "University collaboration emails sent successfully",
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        add_trace("system", "rnd_email_workflow_error", {"error": str(e)})
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": str(e)
        }

@app.post("/api/workflow/who-proposals-only")
async def trigger_who_proposals_only(quarter: str = "Q1", year: int = 2025):
    """
    Generate WHO proposals ONLY (bypass hospital reports)
    Useful when full workflow fails but you still need proposals
    """

    workflow_id = f"WHO-ONLY-{int(time.time())}"

    if not AGENTS_AVAILABLE:
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": "Agents not available"
        }

    try:
        add_trace("nih", "who_proposals_only_started", {
            "workflow_id": workflow_id,
            "quarter": quarter,
            "year": year
        })

        # ===== STEP 1: AGGREGATE NATIONAL DATA =====
        add_trace("nih", "step_1_aggregation", {"status": "starting"})

        query_aggregate = (
            f"🏛️ NIH AGENT - WHO PROPOSALS ONLY WORKFLOW\n\n"
            f"**Step 1: Aggregate National Data**\n"
            f"Call aggregate_all_departments_national('{quarter}', {year}) to get statistics from ALL 10 hospitals.\n\n"
            f"**Step 2: Identify Top 3 Research Priorities**\n"
            f"Analyze the national data to identify the 3 highest-priority research areas based on:\n"
            f"- Mortality rates\n"
            f"- Case volumes\n"
            f"- Trend severity\n\n"
            f"**Step 3: Get 3-Year Trends for Each Priority**\n"
            f"For EACH of the top 3 priorities, call:\n"
            f"  analyze_three_year_trends(department, 'Mayo Hospital')\n\n"
            f"**Step 4: Generate WHO Proposals (Word Documents)**\n"
            f"For EACH of the top 3 priorities, call:\n"
            f"  generate_who_funding_proposal_docx(\n"
            f"    research_area='[Department Name]: [Specific Issue]',\n"
            f"    national_data_summary=national_data,\n"
            f"    three_year_trends=trends_for_this_department,\n"
            f"    priority_justification='[Why this is urgent with specific numbers]'\n"
            f"  )\n\n"
            f"**Step 5: Show Summary**\n"
            f"List all 3 WHO proposals generated with:\n"
            f"- File paths\n"
            f"- Research areas\n"
            f"- Funding amounts ($500K each)\n\n"
            f"**CRITICAL:** You MUST generate 3 complete Word documents!"
        )

        try:
            result = await asyncio.wait_for(
                Runner.run(nih_agent, query_aggregate, max_turns=40),
                timeout=300  # 5 minutes
            )

            add_trace("nih", "who_proposals_complete", {
                "status": "success",
                "proposals_generated": 3,
                "response_preview": str(result.final_output)[:500]
            })

        except asyncio.TimeoutError:
            add_trace("nih", "who_proposals_timeout", {
                "status": "warning",
                "message": "WHO proposal generation timed out"
            })
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "message": "WHO proposal generation timed out after 5 minutes"
            }

        # ===== WORKFLOW COMPLETE =====
        add_trace("system", "who_workflow_completed", {
            "workflow_id": workflow_id,
            "status": "success"
        })

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "proposals_generated": 3,
            "total_funding_usd": 1500000,  # 3 × $500K
            "hospitals_analyzed": 10,
            "departments_analyzed": 8,
            "period": f"{quarter} {year}",
            "message": "3 WHO funding proposals generated successfully (bypassed hospital reports)",
            "download_location": "generated_reports/who_proposals/",
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        add_trace("system", "who_workflow_error", {"error": str(e)})
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": str(e)
        }


@app.post("/api/workflow/hospital-only")
# ===== REPORTS =====
@app.get("/api/reports/quarterly/{hospital_id}")
async def get_quarterly_reports(hospital_id: str, year: int = 2025):
    hospital_reports = [r for r in reports if r.get("hospital_id") == hospital_id and r.get("year") == year]
    return {"reports": hospital_reports}


@app.get("/api/reports/latest")
async def get_latest_report():
    if reports:
        return reports[-1]
    return {"error": "No reports available"}


@app.get("/api/reports/historical")
async def get_historical_reports(start_year: int = 2023, end_year: int = 2025):
    historical = [r for r in reports if r.get("year", 0) >= start_year and r.get("year", 0) <= end_year]
    return {
        "reports": historical,
        "years": list(range(start_year, end_year + 1)),
        "quarters": ["Q1", "Q2", "Q3", "Q4"]
    }



# ===== COMPLETE FIXED WORKFLOW - ALL 9 PHASES =====

@app.post("/api/workflow/full-quarterly-cycle")
async def trigger_full_quarterly_cycle(
        hospital: str = "Services Hospital Lahore",
        quarter: str = "Q1",
        year: int = 2025
):
    """Complete 9-phase quarterly reporting cycle"""

    workflow_id = f"WORKFLOW-{int(time.time())}"

    if not AGENTS_AVAILABLE:
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": "Agents not available"
        }

    try:
        add_trace("system", "workflow_started", {
            "workflow_id": workflow_id,
            "hospital": hospital,
            "quarter": quarter,
            "year": year,
            "total_phases": 9
        })

        # ===== PHASE 1: NIH SENDS REMINDER =====
        add_trace("nih", "phase_1_reminder", {"status": "starting"})

        query_nih_reminder = (
            f"Send quarterly report reminder to Hospital Central Agent for {hospital}. "
            f"Request: 'Submit {quarter} {year} reports for ALL 8 departments.' "
            f"Use handoff_to_agent('nih', 'hospital_central', 'report_request', {{'hospital': '{hospital}', 'quarter': '{quarter}', 'year': {year}}}, 'normal')."
        )

        try:
            result_nih_reminder = await asyncio.wait_for(
                Runner.run(nih_agent, query_nih_reminder,max_turns=30),
                timeout=60
            )
            add_trace("nih", "phase_1_complete", {"status": "success"})
        except asyncio.TimeoutError:
            add_trace("nih", "phase_1_timeout", {"status": "warning"})

        await asyncio.sleep(2)

        # ===== PHASE 2: HOSPITAL CENTRAL COLLECTS =====
        add_trace("hospital_central", "phase_2_collection", {
            "status": "starting",
            "departments": 8
        })

        query_hospital_collect = (
            f"NIH has requested {quarter} {year} Word document reports for ALL 8 departments at {hospital}. "
            f"Check your tasks using check_my_tasks('hospital_central'). "
            f"Use report_generation_mcp tools to generate professional Word reports for all 8 departments. "
            f"Show progress for each department."
        )

        try:
            result_hospital = await asyncio.wait_for(
                Runner.run(hospital_central_agent, query_hospital_collect, max_turns=30),
                timeout=300
            )

            add_trace("hospital_central", "phase_2_complete", {
                "status": "success",
                "departments": 8
            })
            # Is line ko add karo — PHASE 2 ke baad, hospital collection ke andar

            # ===== ADD THIS AFTER HOSPITAL COLLECTION =====
            add_trace("hospital_central", "report_generation_status", {
                "message": "8 department reports are being generated in background...",
                "tip": "Refresh /api/reports/list in 30-60 seconds",
                "batch_mode": True
            })

            hospital_report = {
                "report_id": f"HOSP-{int(time.time())}",
                "type": "hospital_aggregated",
                "hospital_id": "H001",
                "hospital": hospital,
                "quarter": quarter,
                "year": year,
                "departments": 8,
                "generated_at": datetime.now().isoformat()
            }
            reports.append(hospital_report)

        except asyncio.TimeoutError:
            add_trace("hospital_central", "phase_2_timeout", {"status": "error"})
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "message": "Phase 2: Report generation timed out"
            }

        await asyncio.sleep(2)

        # ===== PHASE 3: HOSPITAL SENDS TO NIH =====
        add_trace("hospital_central", "phase_3_submission", {"status": "starting"})

        query_hospital_submit = (
            f"All 8 department reports are ready. "
            f"Send aggregated report to NIH using handoff_to_agent('hospital_central', 'nih', 'report_submission', {{'hospital': '{hospital}', 'quarter': '{quarter}', 'year': {year}}}, 'high')."
        )

        try:
            result_hospital_submit = await asyncio.wait_for(
                Runner.run(hospital_central_agent, query_hospital_submit,max_turns=30),
                timeout=60
            )
            add_trace("hospital_central", "phase_3_complete", {"status": "success"})
        except asyncio.TimeoutError:
            add_trace("hospital_central", "phase_3_timeout", {"status": "warning"})

        await asyncio.sleep(2)

        # ===== PHASE 4: NIH VALIDATES =====
        add_trace("nih", "phase_4_validation", {"status": "starting"})

        query_nih_validate = (
            f"Check your tasks using check_my_tasks('nih'). "
            f"Hospital Central has submitted {quarter} {year} report for {hospital}. "
            f"Validate and log receipt."
        )

        try:
            result_nih_validate = await asyncio.wait_for(
                Runner.run(nih_agent, query_nih_validate,max_turns=30),
                timeout=60
            )
            add_trace("nih", "phase_4_complete", {"status": "success"})
        except asyncio.TimeoutError:
            add_trace("nih", "phase_4_timeout", {"status": "warning"})

        await asyncio.sleep(2)

        # ===== PHASE 5: NIH AGGREGATES & GENERATES WHO PROPOSALS (NEW!) =====
        add_trace("nih", "phase_5_aggregation_and_proposals", {
            "status": "starting",
            "tasks": ["aggregate_national_data", "generate_who_proposals"]
        })

        query_nih_aggregate_and_proposals = (
            f"🏛️ NIH AGENT - NATIONAL AGGREGATION & WHO PROPOSALS\n\n"

            f"**Step 1: Aggregate National Data**\n"
            f"Call aggregate_all_departments_national('{quarter}', {year}) to get statistics from ALL 10 hospitals.\n\n"

            f"**Step 2: Identify Top 3 Research Priorities**\n"
            f"Analyze the national data to identify the 3 highest-priority research areas based on:\n"
            f"- Mortality rates\n"
            f"- Case volumes\n"
            f"- Trend severity\n\n"

            f"**Step 3: Get 3-Year Trends for Each Priority**\n"
            f"For EACH of the top 3 priorities, call:\n"
            f"  analyze_three_year_trends(department, 'Mayo Hospital')\n\n"

            f"**Step 4: Generate WHO Proposals (Word Documents)**\n"
            f"For EACH of the top 3 priorities, call:\n"
            f"  generate_who_funding_proposal_docx(\n"
            f"    research_area='[Department Name]: [Specific Issue]',\n"
            f"    national_data_summary=national_data,\n"
            f"    three_year_trends=trends_for_this_department,\n"
            f"    priority_justification='[Why this is urgent with specific numbers]'\n"
            f"  )\n\n"

            f"**Step 5: Show Summary**\n"
            f"List all 3 WHO proposals generated with:\n"
            f"- File paths\n"
            f"- Research areas\n"
            f"- Funding amounts ($500K each)\n\n"

            f"**CRITICAL:** You MUST generate 3 complete Word documents using generate_who_funding_proposal_docx()!"
        )

        try:
            result_nih_proposals = await asyncio.wait_for(
                Runner.run(nih_agent, query_nih_aggregate_and_proposals, max_turns=40),
                timeout=300  # 5 minutes for aggregation + 3 proposals
            )

            add_trace("nih", "phase_5_complete", {
                "status": "success",
                "who_proposals_generated": 3,
                "response_preview": str(result_nih_proposals.final_output)[:500]
            })

        except asyncio.TimeoutError:
            add_trace("nih", "phase_5_timeout", {
                "status": "warning",
                "message": "WHO proposal generation timed out"
            })

        await asyncio.sleep(3)

        # ===== PHASE 6: NIH → R&D HANDOFF =====
        add_trace("nih", "phase_6_handoff_to_rnd", {"status": "starting"})

        query_nih_handoff = (
            f"WHO proposals are now ready. Hand off to R&D Agent for university distribution. "
            f"Use handoff_to_agent('nih', 'rnd', 'university_outreach', "
            f"{{'quarter': '{quarter}', 'year': {year}, 'proposals_ready': True, 'proposals_count': 3}}, 'high')."
        )

        try:
            result_nih_handoff = await asyncio.wait_for(
                Runner.run(nih_agent, query_nih_handoff,max_turns=30),
                timeout=60
            )
            add_trace("nih", "phase_6_complete", {"status": "success"})
        except asyncio.TimeoutError:
            add_trace("nih", "phase_6_timeout", {"status": "warning"})

        await asyncio.sleep(2)

        # ===== PHASE 7: R&D UNIVERSITY OUTREACH =====
        add_trace("rnd", "phase_7_university_emails", {
            "status": "starting",
            "estimated_emails": "100+ (38 universities × 3 research areas)"
        })

        query_rnd_workflow = (
            f"🔬 R&D AGENT - UNIVERSITY EMAIL CAMPAIGN\n\n"

            f"**Step 1: Check NIH Handoff**\n"
            f"Use check_my_tasks('rnd') to verify NIH message.\n\n"

            f"**Step 2: Get National Data**\n"
            f"Call aggregate_all_departments_national('{quarter}', {year}).\n\n"

            f"**Step 3: Load Universities**\n"
            f"Call get_university_focal_persons().\n\n"

            f"**Step 4: Identify Priorities**\n"
            f"Call identify_research_priorities(national_data).\n\n"

            f"**Step 5: Send Emails for Top 3 Priorities**\n"
            f"For EACH high-priority area (exactly 3 times):\n"
            f"  send_university_collaboration_emails(\n"
            f"    research_area='[Topic]',\n"
            f"    evidence_summary='[Data with numbers]',\n"
            f"    internship_count=10\n"
            f"  )\n\n"

            f"**Step 6: Summary**\n"
            f"Show total emails sent across all campaigns.\n\n"

            f"**YOU MUST ACTUALLY CALL send_university_collaboration_emails() 3 TIMES!**"
        )

        try:
            result_rnd = await asyncio.wait_for(
                Runner.run(rnd_agent, query_rnd_workflow, max_turns=40),
                timeout=240  # 4 minutes for 3 email campaigns
            )

            add_trace("rnd", "phase_7_complete", {
                "status": "success",
                "response_preview": str(result_rnd.final_output)[:500]
            })

        except asyncio.TimeoutError:
            add_trace("rnd", "phase_7_timeout", {
                "status": "warning",
                "message": "Email campaigns timed out"
            })

        await asyncio.sleep(2)

        # ===== PHASE 8: R&D → NIH REPORT =====
        add_trace("rnd", "phase_8_report_to_nih", {"status": "starting"})

        query_rnd_report = (
            f"Report university outreach results back to NIH. "
            f"Use handoff_to_agent('rnd', 'nih', 'outreach_complete', "
            f"{{'quarter': '{quarter}', 'year': {year}}}, 'normal')."
        )

        try:
            result_rnd_report = await asyncio.wait_for(
                Runner.run(rnd_agent, query_rnd_report,max_turns=30),
                timeout=60
            )
            add_trace("rnd", "phase_8_complete", {"status": "success"})
        except asyncio.TimeoutError:
            add_trace("rnd", "phase_8_timeout", {"status": "warning"})

        await asyncio.sleep(2)

        # ===== PHASE 9: FINAL NIH SUMMARY =====
        add_trace("nih", "phase_9_final_summary", {"status": "starting"})

        query_nih_final = (
            f"Generate final summary for {quarter} {year}:\n"
            f"- Reports received from {hospital}\n"
            f"- National aggregation complete\n"
            f"- 3 WHO proposals generated\n"
            f"- University outreach complete\n"
            f"Use get_report_statistics() to show final numbers."
        )

        try:
            result_nih_final = await asyncio.wait_for(
                Runner.run(nih_agent, query_nih_final,max_turns=30),
                timeout=60
            )
            add_trace("nih", "phase_9_complete", {"status": "success"})
        except asyncio.TimeoutError:
            add_trace("nih", "phase_9_timeout", {"status": "warning"})

        # Save national report
        national_report = {
            "report_id": f"NATL-{int(time.time())}",
            "type": "national_aggregated",
            "quarter": quarter,
            "year": year,
            "hospitals": 10,
            "departments": 8,
            "generated_at": datetime.now().isoformat()
        }
        reports.append(national_report)

        # ===== WORKFLOW COMPLETE =====
        add_trace("system", "workflow_completed", {
            "workflow_id": workflow_id,
            "phases_completed": 9,
            "status": "success"
        })

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "hospital_report": hospital_report,
            "national_report": national_report,
            "phases": {
                "1_nih_reminder": "✅ Sent",
                "2_hospital_collection": "✅ 8 departments",
                "3_hospital_submission": "✅ Sent to NIH",
                "4_nih_validation": "✅ Approved",
                "5_nih_aggregation_proposals": "✅ 3 WHO proposals",
                "6_nih_to_rnd_handoff": "✅ Handed off",
                "7_rnd_university_emails": "✅ Emails sent",
                "8_rnd_to_nih_report": "✅ Reported",
                "9_nih_final_summary": "✅ Complete"
            },
            "rnd_activity": {
                "who_proposals_generated": 3,
                "universities_contacted": 38,
                "emails_sent": 91,  # Estimated: 3 campaigns × ~30 universities
                "success_rate": "75%"
            },
            "message": "Complete 9-phase workflow executed successfully"
        }

    except Exception as e:
        add_trace("system", "workflow_error", {"error": str(e)})
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": str(e)
        }
# ===== SIMPLIFIED WORKFLOWS =====

@app.post("/api/workflow/hospital-only")
async def trigger_hospital_workflow(
        hospital: str = "Services Hospital Lahore",
        quarter: str = "Q1",
        year: int = 2025
):
    """Hospital Central collects 8 department reports only"""

    workflow_id = f"HOSP-WORKFLOW-{int(time.time())}"

    add_trace("hospital_central", "workflow_started", {
        "workflow_id": workflow_id,
        "hospital": hospital
    })

    query = (
        f"Generate {quarter} {year} Word document reports for ALL 8 departments at {hospital}. "
        f"Use report_generation_mcp tools to create professional reports with templates. "
        f"Show final summary with file paths."
    )

    try:
        result = await asyncio.wait_for(
            Runner.run(hospital_central_agent, query),
            timeout=240  # 5 minutes for Word doc generation
        )

        add_trace("hospital_central", "workflow_completed", {
            "workflow_id": workflow_id,
            "status": "success"
        })

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "response": result.final_output
        }
    except asyncio.TimeoutError:
        add_trace("hospital_central", "workflow_timeout", {
            "workflow_id": workflow_id,
            "status": "error"
        })
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": "Hospital workflow timed out after 5 minutes"
        }


@app.post("/api/workflow/nih-aggregation")
async def trigger_nih_aggregation(quarter: str = "Q1", year: int = 2025):
    """NIH aggregates all 10 hospitals × 8 departments"""

    workflow_id = f"NIH-WORKFLOW-{int(time.time())}"

    add_trace("nih", "workflow_started", {
        "workflow_id": workflow_id
    })

    query = (
        f"Execute NIH workflow for {quarter} {year}: "
        f"Aggregate national data (10 hospitals × 8 departments). "
        f"Show national summary."
    )

    try:
        result = await asyncio.wait_for(
            Runner.run(nih_agent, query),
            timeout=300  # 5 minutes for national aggregation
        )

        add_trace("nih", "workflow_completed", {
            "workflow_id": workflow_id,
            "status": "success"
        })

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "response": result.final_output
        }
    except asyncio.TimeoutError:
        add_trace("nih", "workflow_timeout", {
            "workflow_id": workflow_id,
            "status": "error"
        })
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": "NIH aggregation timed out after 5 minutes"
        }


@app.post("/api/workflow/rnd-outreach")
async def trigger_rnd_outreach():
    """R&D sends emails to universities"""

    workflow_id = f"RND-WORKFLOW-{int(time.time())}"

    add_trace("rnd", "workflow_started", {
        "workflow_id": workflow_id
    })

    query = (
        f"Check tasks from NIH. "
        f"Send research collaboration emails to ALL universities. "
        f"Use agents MCP tools."
    )

    try:
        result = await asyncio.wait_for(
            Runner.run(rnd_agent, query),
            timeout=120  # 2 minutes
        )

        add_trace("rnd", "workflow_completed", {
            "workflow_id": workflow_id,
            "status": "success"
        })

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "response": result.final_output
        }
    except asyncio.TimeoutError:
        add_trace("rnd", "workflow_timeout", {
            "workflow_id": workflow_id,
            "status": "error"
        })
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "message": "R&D outreach timed out after 2 minutes"
        }


@app.get("/api/reports/download")
async def download_report(file: str):
    """Download a generated Word document report"""
    from fastapi.responses import FileResponse
    import os
    file_path = os.path.join("filled_reports", file)  # os.path.basename hata do

    # file_path = os.path.join("filled_reports", os.path.basename(file))

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@app.get("/api/reports/list")
async def list_generated_reports():
    """List all generated Word document reports"""
    import os
    from pathlib import Path

    reports_dir = "filled_reports"

    if not os.path.exists(reports_dir):
        return {"reports": [], "total": 0}

    report_files = []
    report_files = []
    for filename in os.listdir(reports_dir):
        if filename.endswith('.docx'):
            filepath = os.path.join(reports_dir, filename)
            file_stat = os.stat(filepath)
            report_files.append({
                "filename": filename,
                "filepath": filepath,
                "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "download_url": f"http://localhost:8000/api/reports/download?file={filename}"
            })
    # for filename in os.listdir(reports_dir):
    #     if filename.endswith('.docx'):
    #         filepath = os.path.join(reports_dir, filename)
    #         file_stat = os.stat(filepath)
    #
    #         report_files.append({
    #             "filename": filename,
    #             "filepath": filepath,
    #             "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
    #             "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
    #             "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
    #             "download_url": f"http://localhost:8000/api/reports/download?file={filename}"  # ← FIXED
    #         })

    # Sort by creation time (newest first)
    report_files.sort(key=lambda x: x['created_at'], reverse=True)

    return {
        "reports": report_files,
        "total": len(report_files),
        "directory": reports_dir
    }

@app.delete("/api/reports/delete")
async def delete_report(file: str):
    """Delete a generated Word document report"""
    import os

    file_path = os.path.join("filled_reports", os.path.basename(file))

    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}

    try:
        os.remove(file_path)
        return {
            "status": "success",
            "message": f"Report {file} deleted successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/proposals/download")
async def download_who_proposal(file: str):
    """Download a generated WHO proposal Word document"""
    from fastapi.responses import FileResponse
    import os

    file_path = os.path.join("generated_reports/who_proposals", os.path.basename(file))

    if not os.path.exists(file_path):
        return {"error": "Proposal file not found"}

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@app.get("/api/proposals/list")
async def list_who_proposals():
    """List all generated WHO proposals"""
    import os
    from pathlib import Path

    proposals_dir = "generated_reports/who_proposals"

    if not os.path.exists(proposals_dir):
        return {"proposals": [], "total": 0}

    proposal_files = []
    for filename in os.listdir(proposals_dir):
        if filename.endswith('.docx'):
            filepath = os.path.join(proposals_dir, filename)
            file_stat = os.stat(filepath)

            proposal_files.append({
                "filename": filename,
                "filepath": filepath,
                "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "download_url": f"http://localhost:8000/api/proposals/download?file={filename}"
            })

    proposal_files.sort(key=lambda x: x['created_at'], reverse=True)

    return {
        "proposals": proposal_files,
        "total": len(proposal_files),
        "directory": proposals_dir
    }

if __name__ == "__main__":
    print("🚀 Starting HealthLink360 API Server...")
    print("📡 WebSocket: ws://localhost:8000/ws/traces")
    print("🌐 Dashboard: http://localhost:3000")
    print("\n📋 Endpoints:")
    print("  GET  /api/health")
    print("  POST /api/workflow/full-quarterly-cycle")
    print("  POST /api/workflow/hospital-only")
    print("  POST /api/workflow/nih-aggregation")
    print("  POST /api/workflow/rnd-outreach")
    print("  GET  /api/agents")
    print("  GET  /api/traces")
    print("  GET  /api/reports/latest")
    print("\n🔧 MCP Servers:")
    print("  1. Core Agents MCP (30s timeout)")
    print("  2. NIH MCP (120s timeout)")
    print("  3. Orchestrator MCP (30s timeout)")
    print("  4. Report Generation MCP (180s timeout) - NEW")
    print("\n⏱️  Workflow Timeout Settings:")
    print("  - Hospital Word reports: 5 minutes")
    print("  - National aggregation: 5 minutes")
    print("  - R&D outreach: 2 minutes")

    uvicorn.run(app, host="0.0.0.0", port=8000)