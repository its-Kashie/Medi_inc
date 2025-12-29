import os
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

# ===== MongoDB Setup =====
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["healthlink360"]
agents_collection = db["agent_settings"]
memory_collection = db["agent_memory"]

# ===== FastAPI Setup =====
app = FastAPI(title="HealthLink360 Settings API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Data Models =====
class ToolSetting(BaseModel):
    tool_name: str
    enabled: bool
    parameters: Dict = {}
    description: str = ""


class AgentSettings(BaseModel):
    agent_id: str
    agent_name: str
    enabled: bool = True
    tools: List[ToolSetting]
    memory_enabled: bool = True
    max_memory_items: int = 100
    auto_clear_memory: bool = False
    metadata: Dict = {}


class MemoryEntry(BaseModel):
    agent_id: str
    session_id: str
    role: str
    content: str


# ===== Agent Tool Definitions (from MCP servers) =====
AGENT_TOOLS_REGISTRY = {
    "tracking": [
        {"name": "dispatch_nearest_ambulance", "description": "Dispatch nearest available ambulance"},
        {"name": "release_ambulance", "description": "Release ambulance back to available pool"},
        {"name": "nearest_hospital_fallback", "description": "Find nearest hospital (degraded mode)"},
        {"name": "pharmacy_request", "description": "Check pharmacy stock and approve prescription"},
    ],
    "maternal": [
        {"name": "maternal_emergency", "description": "Emergency handoff to tracking agent"},
        {"name": "hms_register_patient", "description": "Register patient with Hospital HMS"},
        {"name": "nadra_birth_register", "description": "Register birth with NADRA"},
        {"name": "schedule_postpartum_vaccination", "description": "Schedule postpartum and newborn vaccinations"},
        {"name": "maternal_pharmacy_handoff", "description": "Pharmacy handoff for supplements"},
    ],
    "mental": [
        {"name": "assess_stress_level", "description": "AI-based stress assessment"},
        {"name": "assign_therapist", "description": "Assign nearest or most relevant therapist"},
        {"name": "schedule_followup", "description": "Schedule follow-up therapy session"},
        {"name": "mental_emergency_hotline", "description": "Emergency mental health hotline dispatch"},
    ],
    "pharmacy": [
        {"name": "check_pharmacy_stock", "description": "Check medicine stock at specific facility"},
        {"name": "predict_medicine_shortage", "description": "Predict shortage across all facilities"},
        {"name": "generate_purchase_order", "description": "Auto-generate purchase order"},
        {"name": "reallocate_medicine", "description": "Reallocate stock between facilities"},
        {"name": "create_patient_prescription", "description": "Create prescription for patient"},
        {"name": "detect_abnormal_consumption", "description": "Detect potential medicine abuse"},
    ],
    "criminal": [
        {"name": "classify_injury_local", "description": "Local AI-powered injury classification"},
        {"name": "create_case_report", "description": "Create criminal case report with auto-classification"},
        {"name": "report_to_police", "description": "Auto-report suspicious case to police"},
        {"name": "verify_identity_nadra", "description": "Verify identity via NADRA"},
        {"name": "collect_medical_evidence", "description": "Collect and store medical evidence"},
        {"name": "transfer_evidence_to_forensics", "description": "Transfer evidence to forensic department"},
        {"name": "get_police_jurisdiction", "description": "Get appropriate police jurisdiction"},
        {"name": "pseudonymize_case_data", "description": "Pseudonymize sensitive case data"},
    ],
    "waste": [
        {"name": "monitor_container_levels", "description": "Monitor all container levels"},
        {"name": "schedule_pickup", "description": "Schedule automatic pickup before overflow"},
        {"name": "optimize_collection_route", "description": "Optimize routing for garbage collection"},
        {"name": "handle_pharmaceutical_waste", "description": "Special handling for pharmaceutical waste"},
        {"name": "sync_with_lwmc", "description": "Sync waste management data with LWMC"},
        {"name": "get_container_details", "description": "Get detailed container information"},
        {"name": "update_container_level", "description": "Update container level (IoT sensor)"},
        {"name": "notify_hospital_pickup", "description": "Send pickup notification to hospital"},
    ],
    "research": [
        {"name": "aggregate_hospital_data", "description": "Aggregate hospital data trends"},
        {"name": "detect_high_demand_fields", "description": "Detect high-demand medical fields"},
        {"name": "assign_internships", "description": "Assign internships based on demand"},
        {"name": "send_university_email", "description": "Send research proposal to universities"},
    ]
}


# ===== Initialize Default Settings =====
def initialize_agent_settings():
    """Initialize default settings for all hospital_agents if not exist"""
    for agent_id, tools in AGENT_TOOLS_REGISTRY.items():
        existing = agents_collection.find_one({"agent_id": agent_id})

        if not existing:
            default_settings = {
                "agent_id": agent_id,
                "agent_name": agent_id.capitalize() + " Agent",
                "enabled": True,
                "tools": [
                    {
                        "tool_name": tool["name"],
                        "enabled": True,
                        "parameters": {},
                        "description": tool["description"]
                    }
                    for tool in tools
                ],
                "memory_enabled": True,
                "max_memory_items": 100,
                "auto_clear_memory": False,
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            agents_collection.insert_one(default_settings)
            print(f"✅ Initialized settings for {agent_id}")


# ===== API Endpoints =====

@app.on_event("startup")
async def startup_event():
    """Initialize settings on startup"""
    print("🚀 Settings Manager Starting...")
    initialize_agent_settings()
    print("✅ All agent settings initialized")


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "HealthLink360 Settings Manager",
        "agents_count": agents_collection.count_documents({})
    }


@app.get("/api/settings/hospital_agents")
async def get_all_agents():
    """Get all agent settings"""
    agents = list(agents_collection.find({}, {"_id": 0}))
    return {"hospital_agents": agents, "total": len(agents)}


@app.get("/api/settings/agent/{agent_id}")
async def get_agent_settings(agent_id: str):
    """Get settings for specific agent"""
    settings = agents_collection.find_one({"agent_id": agent_id}, {"_id": 0})

    if not settings:
        raise HTTPException(status_code=404, detail="Agent not found")

    return settings


@app.put("/api/settings/agent/{agent_id}")
async def update_agent_settings(agent_id: str, settings: AgentSettings):
    """Update agent settings"""
    if agent_id != settings.agent_id:
        raise HTTPException(status_code=400, detail="Agent ID mismatch")

    settings_dict = settings.dict()
    settings_dict["metadata"]["updated_at"] = datetime.utcnow().isoformat()

    result = agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": settings_dict},
        upsert=True
    )

    return {
        "status": "success",
        "agent_id": agent_id,
        "modified": result.modified_count > 0,
        "message": "Settings updated successfully"
    }


@app.patch("/api/settings/agent/{agent_id}/tool/{tool_name}")
async def toggle_tool(agent_id: str, tool_name: str, enabled: bool):
    """Toggle specific tool on/off"""
    result = agents_collection.update_one(
        {"agent_id": agent_id, "tools.tool_name": tool_name},
        {"$set": {
            "tools.$.enabled": enabled,
            "metadata.updated_at": datetime.utcnow().isoformat()
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent or tool not found")

    return {
        "status": "success",
        "agent_id": agent_id,
        "tool_name": tool_name,
        "enabled": enabled
    }


@app.patch("/api/settings/agent/{agent_id}/enable")
async def toggle_agent(agent_id: str, enabled: bool):
    """Enable/disable entire agent"""
    result = agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": {
            "enabled": enabled,
            "metadata.updated_at": datetime.utcnow().isoformat()
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "status": "success",
        "agent_id": agent_id,
        "enabled": enabled
    }


# ===== Memory Management =====

@app.post("/api/memory/{agent_id}")
async def add_memory(agent_id: str, entry: MemoryEntry):
    """Add memory entry for agent"""
    settings = agents_collection.find_one({"agent_id": agent_id})

    if not settings or not settings.get("memory_enabled"):
        raise HTTPException(status_code=400, detail="Memory disabled for this agent")

    memory_doc = {
        "agent_id": agent_id,
        "session_id": entry.session_id,
        "role": entry.role,
        "content": entry.content,
        "timestamp": datetime.utcnow().isoformat()
    }

    memory_collection.insert_one(memory_doc)

    # Auto-clear if limit exceeded
    max_items = settings.get("max_memory_items", 100)
    count = memory_collection.count_documents({"agent_id": agent_id, "session_id": entry.session_id})

    if count > max_items:
        # Delete oldest entries
        oldest = list(memory_collection.find(
            {"agent_id": agent_id, "session_id": entry.session_id}
        ).sort("timestamp", 1).limit(count - max_items))

        for doc in oldest:
            memory_collection.delete_one({"_id": doc["_id"]})

    return {"status": "success", "message": "Memory added"}


@app.get("/api/memory/{agent_id}/{session_id}")
async def get_memory(agent_id: str, session_id: str, limit: int = 50):
    """Get memory for agent session"""
    memories = list(memory_collection.find(
        {"agent_id": agent_id, "session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit))

    return {
        "agent_id": agent_id,
        "session_id": session_id,
        "count": len(memories),
        "memories": list(reversed(memories))
    }


@app.delete("/api/memory/{agent_id}/{session_id}")
async def clear_memory(agent_id: str, session_id: str):
    """Clear memory for agent session"""
    result = memory_collection.delete_many({
        "agent_id": agent_id,
        "session_id": session_id
    })

    return {
        "status": "success",
        "deleted_count": result.deleted_count
    }


@app.get("/api/memory/stats/{agent_id}")
async def get_memory_stats(agent_id: str):
    """Get memory statistics for agent"""
    total = memory_collection.count_documents({"agent_id": agent_id})
    sessions = memory_collection.distinct("session_id", {"agent_id": agent_id})

    return {
        "agent_id": agent_id,
        "total_memories": total,
        "active_sessions": len(sessions),
        "sessions": sessions
    }


# ===== Tools Registry =====

@app.get("/api/tools/registry")
async def get_tools_registry():
    """Get all available tools from registry"""
    return {"tools": AGENT_TOOLS_REGISTRY}


@app.get("/api/tools/registry/{agent_id}")
async def get_agent_tools_registry(agent_id: str):
    """Get available tools for specific agent"""
    if agent_id not in AGENT_TOOLS_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found in registry")

    return {
        "agent_id": agent_id,
        "tools": AGENT_TOOLS_REGISTRY[agent_id]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)