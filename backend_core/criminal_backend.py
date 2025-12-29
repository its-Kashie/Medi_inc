# criminal_backend.py - FastAPI Backend for Criminal Agent
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Import your criminal agent
from criminal_agent import criminal_agent, run_with_retry, orchestrator_mcp, domain_mcp, redact_pii

app = FastAPI(title="Criminal Forensics API")

# CORS for HTML frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class CaseRequest(BaseModel):
    description: str
    user_id: Optional[str] = "doctor_001"


class FollowupRequest(BaseModel):
    case_id: str
    action: str  # "send_reminder", "view_report", "close_case"
    closure_notes: Optional[str] = None


# In-memory storage (production mein database use karo)
recent_cases = []
chat_history = []


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Criminal Forensics Backend",
        "agent": "CriminalCaseAgent",
        "version": "1.0.0"
    }


@app.post("/api/criminal/scan")
async def scan_case(request: CaseRequest):
    """
    Main endpoint - HTML se case description receive karo
    Criminal agent ko run karo
    Response return karo
    """
    try:
        # Run criminal agent with user query
        result = await run_with_retry(criminal_agent, request.description)
        agent_response = result.final_output if hasattr(result, "final_output") else str(result)

        # Redact PII from response
        safe_response = redact_pii(agent_response)

        # Extract case details from response (basic parsing)
        case_detected = any(keyword in request.description.lower() for keyword in
                            ["mar", "chaku", "rape", "husband", "attack", "violence", "assault"])

        # Save to history
        case_entry = {
            "timestamp": datetime.now().isoformat(),
            "description": request.description[:100],  # Truncate for storage
            "agent_response": safe_response,
            "case_detected": case_detected,
            "user_id": request.user_id
        }
        recent_cases.append(case_entry)
        chat_history.append({
            "role": "user",
            "content": request.description,
            "timestamp": datetime.now().isoformat()
        })
        chat_history.append({
            "role": "agent",
            "content": safe_response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "status": "success",
            "case_detected": case_detected,
            "agent_response": safe_response,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.post("/api/criminal/followup")
async def handle_followup(request: FollowupRequest):
    """
    Handle 6-month follow-up actions
    """
    try:
        if request.action == "send_reminder":
            query = f"Case {request.case_id} ki 6-month follow-up reminder police ko bhejo. Email: hafizalaibafaisal@gmail.com"
        elif request.action == "view_report":
            query = f"Case {request.case_id} ki complete follow-up report generate karo with evidence, duration, and closure status."
        elif request.action == "close_case":
            query = f"Case {request.case_id} ko closed mark karo. Closure notes: {request.closure_notes or 'Case resolved'}"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        result = await run_with_retry(criminal_agent, query)
        agent_response = result.final_output if hasattr(result, "final_output") else str(result)

        return {
            "status": "success",
            "action": request.action,
            "case_id": request.case_id,
            "agent_response": redact_pii(agent_response),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Follow-up error: {str(e)}")


@app.get("/api/criminal/history")
async def get_history(limit: int = 10):
    """Get recent case history"""
    return {
        "total_cases": len(recent_cases),
        "recent_cases": recent_cases[-limit:],
        "chat_history": chat_history[-limit * 2:]  # Last N user + agent messages
    }


@app.get("/api/criminal/stats")
async def get_stats():
    """Get dashboard statistics"""
    total_cases = len(recent_cases)
    detected_cases = sum(1 for case in recent_cases if case["case_detected"])

    return {
        "total_cases": total_cases,
        "cases_detected": detected_cases,
        "auto_reported": detected_cases,  # Assuming all detected cases are reported
        "followups_scheduled": detected_cases,
        "success_rate": round((detected_cases / total_cases * 100) if total_cases > 0 else 0, 1)
    }


# Startup event - connect MCPs
@app.on_event("startup")
async def startup_event():
    """Initialize MCPs on startup"""
    print("🚀 Starting Criminal Forensics Backend...")
    try:
        await orchestrator_mcp.connect()
        await domain_mcp.connect()
        print("✅ Both MCP servers connected")
        print("📡 Backend ready at http://localhost:8002")
        print("🌐 HTML frontend can now connect!")
    except Exception as e:
        print(f"⚠️ MCP connection failed: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down...")
    await orchestrator_mcp.cleanup()
    await domain_mcp.cleanup()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)