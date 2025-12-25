# agent_orchestrator_mcp.py - Inter-Agent Communication Hub
import json
import time
from functools import wraps
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import os
# Add at top of EVERY MCP file:
import sys
os.environ['MCP_CLIENT_TIMEOUT'] = '10'
def debug_log(msg):
    """Log to STDERR only (STDOUT reserved for MCP)"""
    print(msg, file=sys.stderr, flush=True)

# Replace ALL print() calls with debug_log()
debug_log("✅ MCP initialized")
# ===== MCP Server =====
mcp = FastMCP("Agent Orchestrator - Inter-Agent Communication Hub")

# ===== AGENT REGISTRY =====
AGENT_REGISTRY = {
    # ===== EXISTING AGENTS =====
    "tracking": {
        "name": "TrackingAgent",
        "capabilities": [
            "dispatch_nearest_ambulance",
            "release_ambulance",
            "nearest_hospital_fallback"
        ],
        "status": "active",
        "registered_at": None
    },
    "maternal": {
        "name": "MaternalAgent",
        "capabilities": [
            "maternal_emergency",
            "hms_register_patient",
            "nadra_birth_register",
            "schedule_postpartum_vaccination",
            "maternal_pharmacy_handoff"
        ],
        "status": "active",
        "registered_at": None
    },
    "mental": {
        "name": "MentalHealthAgent",
        "capabilities": [
            "assess_stress_level",
            "assign_therapist",
            "schedule_followup",
            "mental_emergency_hotline"
        ],
        "status": "active",
        "registered_at": None
    },
    "pharmacy": {
        "name": "PharmacyAgent",
        "capabilities": [
            "check_pharmacy_stock",
            "predict_medicine_shortage",
            "generate_purchase_order",
            "reallocate_medicine",
            "create_patient_prescription"
        ],
        "status": "active",
        "registered_at": None
    },
    "research": {
        "name": "ResearchDevAgent",
        "capabilities": [
            "aggregate_hospital_data",
            "detect_high_demand_fields",
            "assign_internships",
            "send_university_email"
        ],
        "status": "active",
        "registered_at": None
    },
    "criminal": {
        "name": "CriminalCaseAgent",
        "capabilities": [
            "classify_injury_local",
            "create_case_report",
            "report_to_police",
            "verify_identity_nadra",
            "collect_medical_evidence",
            "transfer_evidence_to_forensics"
        ],
        "status": "active",
        "registered_at": None
    },
    "waste": {
        "name": "WasteManagementAgent",
        "capabilities": [
            "monitor_container_levels",
            "schedule_pickup",
            "optimize_collection_route",
            "handle_pharmaceutical_waste",
            "sync_with_lwmc"
        ],
        "status": "active",
        "registered_at": None
    },

    # ===== NEW: QUARTERLY REPORTING AGENTS ===== ✅
    "hospital_central": {
        "name": "HospitalCentralAgent",
        "capabilities": [
            "collect_department_reports",
            "generate_hospital_aggregate",
            "submit_to_nih",
            "coordinate_8_departments"
        ],
        "status": "active",
        "registered_at": None
    },
    "nih": {
        "name": "NIHAgent",
        "capabilities": [
            "aggregate_national_statistics",
            "validate_hospital_reports",
            "generate_who_proposals",
            "analyze_three_year_trends",
            "send_quarterly_reminders"
        ],
        "status": "active",
        "registered_at": None
    },
    "rnd": {
        "name": "ResearchAndDevelopmentAgent",
        "capabilities": [
            "send_university_emails",
            "identify_research_priorities",
            "coordinate_with_orics",
            "manage_internship_programs"
        ],
        "status": "active",
        "registered_at": None
    }
}

# ===== MESSAGE QUEUE =====
MESSAGE_QUEUE = []

# ===== HANDOFF HISTORY (for audit) =====
HANDOFF_HISTORY = []

# ===== TRACE LOGGING =====
TRACE_LOG_FILE = "orchestrator_trace.json"
trace_logs = []


def log_orchestrator_action(action_type, data):
    """Log orchestrator actions for tracing"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "data": data
    }
    trace_logs.append(entry)

    with open(TRACE_LOG_FILE, "w") as f:
        json.dump(trace_logs, f, indent=2)


# ===== INTER-AGENT COMMUNICATION TOOLS =====

@mcp.tool()
def handoff_to_agent(
        from_agent: str,
        to_agent: str,
        task_type: str,
        context: dict,
        priority: str = "normal"
) -> dict:
    """
    🔄 Handoff task from one agent to another

    Args:
        from_agent: Source agent (maternal, tracking, mental, etc.)
        to_agent: Target agent
        task_type: Type of task (emergency_dispatch, ambulance_request, etc.)
        context: Task context (patient_id, location, emergency_type, etc.)
        priority: urgent, high, normal, low

    Returns:
        Handoff confirmation with handoff_id
    """

    # Validate agents
    if to_agent not in AGENT_REGISTRY:
        return {
            "status": "error",
            "message": f"Agent '{to_agent}' not found in registry"
        }

    if AGENT_REGISTRY[to_agent]["status"] != "active":
        return {
            "status": "error",
            "message": f"Agent '{to_agent}' is not active"
        }

    # Create handoff
    handoff_id = f"HANDOFF-{int(time.time() * 1000)}"

    handoff_message = {
        "handoff_id": handoff_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "task_type": task_type,
        "context": context,
        "priority": priority,
        "status": "pending",
        "created_at": time.time(),
        "created_at_iso": datetime.now().isoformat(),
        "expires_at": time.time() + 3600  # 1 hour expiry
    }

    # Add to queue
    MESSAGE_QUEUE.append(handoff_message)
    HANDOFF_HISTORY.append(handoff_message)

    # Log action
    log_orchestrator_action("handoff_created", {
        "handoff_id": handoff_id,
        "from": from_agent,
        "to": to_agent,
        "task": task_type,
        "priority": priority
    })

    return {
        "status": "handoff_created",
        "handoff_id": handoff_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "to_agent_full_name": AGENT_REGISTRY[to_agent]["name"],
        "to_agent_capabilities": AGENT_REGISTRY[to_agent]["capabilities"],
        "priority": priority,
        "message": f"Task handed off to {AGENT_REGISTRY[to_agent]['name']}",
        "queue_position": len([m for m in MESSAGE_QUEUE if m["status"] == "pending"])
    }


@mcp.tool()
def check_my_tasks(agent_name: str) -> dict:
    """
    📥 Check pending handoffs for an agent

    Args:
        agent_name: Agent name (tracking, maternal, mental, etc.)

    Returns:
        List of pending handoffs
    """

    # Get pending tasks
    pending = [
        msg for msg in MESSAGE_QUEUE
        if msg["to_agent"] == agent_name and msg["status"] == "pending"
    ]

    # Sort by priority
    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    pending.sort(key=lambda x: priority_order.get(x["priority"], 2))

    # Log action
    log_orchestrator_action("tasks_checked", {
        "agent": agent_name,
        "pending_count": len(pending)
    })

    return {
        "agent": agent_name,
        "agent_full_name": AGENT_REGISTRY.get(agent_name, {}).get("name", "Unknown"),
        "pending_count": len(pending),
        "tasks": pending,
        "checked_at": time.time(),
        "checked_at_iso": datetime.now().isoformat()
    }


@mcp.tool()
def complete_task(handoff_id: str, result: dict, completed_by: str) -> dict:
    """
    ✅ Mark handoff as completed

    Args:
        handoff_id: Handoff ID to complete
        result: Result data from completing agent
        completed_by: Agent name who completed the task

    Returns:
        Completion confirmation
    """

    # Find handoff
    for msg in MESSAGE_QUEUE:
        if msg["handoff_id"] == handoff_id:
            msg["status"] = "completed"
            msg["result"] = result
            msg["completed_at"] = time.time()
            msg["completed_at_iso"] = datetime.now().isoformat()
            msg["completed_by"] = completed_by

            # Log action
            log_orchestrator_action("task_completed", {
                "handoff_id": handoff_id,
                "completed_by": completed_by,
                "from_agent": msg["from_agent"],
                "to_agent": msg["to_agent"]
            })

            return {
                "status": "success",
                "handoff_id": handoff_id,
                "completed_at": msg["completed_at"],
                "completed_at_iso": msg["completed_at_iso"],
                "completed_by": completed_by,
                "result": result,
                "message": f"Task completed by {AGENT_REGISTRY.get(completed_by, {}).get('name', completed_by)}"
            }

    return {
        "status": "error",
        "message": f"Handoff {handoff_id} not found"
    }


@mcp.tool()
def query_agent_capabilities(agent_name: str) -> dict:
    """
    🔍 Check what an agent can do

    Args:
        agent_name: Agent to query (tracking, maternal, etc.)

    Returns:
        Agent capabilities and status
    """

    if agent_name not in AGENT_REGISTRY:
        return {
            "status": "not_found",
            "message": f"Agent '{agent_name}' not in registry",
            "available_agents": list(AGENT_REGISTRY.keys())
        }

    agent = AGENT_REGISTRY[agent_name]

    return {
        "agent_name": agent_name,
        "full_name": agent["name"],
        "capabilities": agent["capabilities"],
        "status": agent["status"],
        "available": agent["status"] == "active",
        "registered_at": agent.get("registered_at")
    }


@mcp.tool()
def get_agent_status(agent_name: str = None) -> dict:
    """
    📊 Get status of one or all agents

    Args:
        agent_name: Specific agent (None = all agents)

    Returns:
        Agent status information
    """

    if agent_name:
        if agent_name not in AGENT_REGISTRY:
            return {"status": "not_found", "message": f"Agent '{agent_name}' not found"}

        return {
            "agent": agent_name,
            **AGENT_REGISTRY[agent_name]
        }

    # Return all agents
    return {
        "total_agents": len(AGENT_REGISTRY),
        "active_agents": len([a for a in AGENT_REGISTRY.values() if a["status"] == "active"]),
        "agents": AGENT_REGISTRY
    }


@mcp.tool()
def send_agent_message(
        from_agent: str,
        to_agent: str,
        message: str,
        data: dict = None
) -> dict:
    """
    💬 Send direct message to another agent

    Args:
        from_agent: Sender agent
        to_agent: Receiver agent
        message: Text message
        data: Optional structured data

    Returns:
        Message confirmation
    """

    if to_agent not in AGENT_REGISTRY:
        return {
            "status": "error",
            "message": f"Agent '{to_agent}' not found"
        }

    message_id = f"MSG-{int(time.time() * 1000)}"

    agent_message = {
        "message_id": message_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message": message,
        "data": data or {},
        "status": "sent",
        "created_at": time.time(),
        "created_at_iso": datetime.now().isoformat()
    }

    MESSAGE_QUEUE.append(agent_message)

    # Log action
    log_orchestrator_action("message_sent", {
        "message_id": message_id,
        "from": from_agent,
        "to": to_agent
    })

    return {
        "status": "message_sent",
        "message_id": message_id,
        "from_agent": from_agent,
        "to_agent": AGENT_REGISTRY[to_agent]["name"],
        "sent_at": agent_message["created_at_iso"]
    }


@mcp.tool()
def broadcast_message(
        from_agent: str,
        message: str,
        data: dict = None,
        target_agents: list = None
) -> dict:
    """
    📢 Broadcast message to multiple agents

    Args:
        from_agent: Source agent
        message: Broadcast message
        data: Optional data
        target_agents: List of agent names (None = all)

    Returns:
        Broadcast confirmation
    """

    if target_agents is None:
        target_agents = list(AGENT_REGISTRY.keys())

    broadcast_id = f"BROADCAST-{int(time.time() * 1000)}"

    sent_count = 0
    for agent in target_agents:
        if agent in AGENT_REGISTRY and agent != from_agent:
            MESSAGE_QUEUE.append({
                "message_id": f"{broadcast_id}-{agent}",
                "broadcast_id": broadcast_id,
                "from_agent": from_agent,
                "to_agent": agent,
                "message": message,
                "data": data or {},
                "status": "sent",
                "created_at": time.time(),
                "created_at_iso": datetime.now().isoformat()
            })
            sent_count += 1

    # Log action
    log_orchestrator_action("broadcast_sent", {
        "broadcast_id": broadcast_id,
        "from": from_agent,
        "recipients": sent_count
    })

    return {
        "status": "broadcast_sent",
        "broadcast_id": broadcast_id,
        "from_agent": from_agent,
        "recipients_count": sent_count,
        "recipients": target_agents
    }


# ===== RESOURCES =====

@mcp.resource("trace://orchestrator/queue")
def message_queue_resource():
    """📨 View current message queue"""
    return {
        "total_messages": len(MESSAGE_QUEUE),
        "pending": len([m for m in MESSAGE_QUEUE if m.get("status") == "pending"]),
        "completed": len([m for m in MESSAGE_QUEUE if m.get("status") == "completed"]),
        "recent_messages": MESSAGE_QUEUE[-10:]  # Last 10
    }


@mcp.resource("trace://orchestrator/history")
def handoff_history_resource():
    """📜 View handoff history"""
    return {
        "total_handoffs": len(HANDOFF_HISTORY),
        "recent_handoffs": HANDOFF_HISTORY[-20:]  # Last 20
    }


@mcp.resource("trace://orchestrator/agents")
def agents_registry_resource():
    """👥 View agent registry"""
    return {
        "total_agents": len(AGENT_REGISTRY),
        "agents": AGENT_REGISTRY
    }


if __name__ == "__main__":
    mcp.run()