# backend.py - SIMPLIFIED (No MCP connection needed)
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
from pathlib import Path
import json

# ===== Import Real Agents =====
try:
    from waste_agent import waste_agent
    from hospital_agents import Runner

    AGENTS_AVAILABLE = True
    print("✅ Waste agent imported successfully!")

except ImportError as e:
    print(f"❌ Error importing agent: {e}")
    AGENTS_AVAILABLE = False
    waste_agent = None

# ===== FastAPI Setup =====
app = FastAPI(title="Waste Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Data Models =====
class ChatMessage(BaseModel):
    agent_id: str
    message: str
    user_id: Optional[str] = "user_001"


class VideoAnalyzeRequest(BaseModel):
    video_path: str


# ===== In-Memory Storage =====
chat_histories: Dict[str, List[Dict]] = {}
agent_traces: Dict[str, List[Dict]] = {}

# ===== Upload Directory =====
UPLOAD_DIR = Path("uploads/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ===== Helper Functions =====
def add_trace(agent_id: str, trace_type: str, data: Dict):
    """Add trace entry for agent"""
    if agent_id not in agent_traces:
        agent_traces[agent_id] = []

    trace_entry = {
        "timestamp": datetime.now().isoformat(),
        "trace_type": trace_type,
        "data": data
    }

    agent_traces[agent_id].append(trace_entry)


def add_to_chat_history(agent_id: str, user_id: str, sender: str, text: str):
    """Add message to chat history"""
    key = f"{agent_id}_{user_id}"
    if key not in chat_histories:
        chat_histories[key] = []

    chat_histories[key].append({
        "sender": sender,
        "text": text,
        "timestamp": datetime.now().isoformat()
    })


# ===== API Endpoints =====

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "Waste Management API",
        "version": "1.0.0",
        "real_agent": AGENTS_AVAILABLE
    }


@app.post("/api/upload-video")
async def upload_video(video: UploadFile = File(...)):
    """Upload video file for analysis"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(video.filename).suffix
        safe_filename = f"hospital_waste_{timestamp}{file_extension}"
        file_path = UPLOAD_DIR / safe_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        print(f"✅ Video uploaded: {file_path}")

        return {
            "status": "success",
            "filename": safe_filename,
            "path": str(file_path),
            "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/analyze-video")
async def analyze_video_endpoint(request: VideoAnalyzeRequest):
    """Analyze uploaded video using Waste Agent"""

    try:
        video_path = Path(request.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video not found: {request.video_path}")

        print(f"\n{'=' * 60}")
        print(f"📹 Analyzing video: {request.video_path}")

        if not AGENTS_AVAILABLE or waste_agent is None:
            raise HTTPException(status_code=503, detail="Waste agent not available")

        # ✅ DIRECT MCP CONTEXT (bypass connection error)
        from waste_agent import waste_mcp

        async with waste_mcp:
            try:
                # Connect MCP
                await waste_mcp.connect()
                print("✅ Waste MCP connected")

                # Call agent
                message = ChatMessage(
                    agent_id="waste",
                    message=f"Analyze this video: {str(video_path.absolute())}. Use analyze_video_waste tool to get waste breakdown.",
                    user_id="system"
                )

                add_to_chat_history("waste", "system", "user", message.message)
                add_trace("waste", "user_message", {"message": message.message})
                add_trace("waste", "processing_started", {"query": message.message})

                # Run agent
                result = await Runner.run(waste_agent, message.message)
                agent_response = result.final_output if hasattr(result, "final_output") else str(result)

                print(f"🤖 Agent response length: {len(agent_response)}")

                add_trace("waste", "processing_completed", {
                    "response_length": len(agent_response),
                    "status": "success"
                })
                add_to_chat_history("waste", "system", "agent", agent_response)

                # Parse response
                import re
                json_match = re.search(r'\{[\s\S]*\}', agent_response)

                if json_match:
                    json_str = json_match.group(0)
                    try:
                        analysis_data = json.loads(json_str)
                        print(f"✅ Parsed analysis data")
                    except json.JSONDecodeError:
                        analysis_data = create_dummy_analysis(video_path)
                else:
                    analysis_data = create_dummy_analysis(video_path)

                print(f"✅ Analysis complete")
                print(f"{'=' * 60}\n")

                return {
                    "status": "success",
                    "analysis": analysis_data
                }

            except Exception as e:
                print(f"❌ MCP error: {e}")
                raise
            finally:
                await waste_mcp.cleanup()

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()

        add_trace("waste", "error", {
            "error_type": type(e).__name__,
            "error_message": str(e)
        })

        return {
            "status": "error",
            "error": str(e),
            "analysis": create_dummy_analysis(Path(request.video_path))
        }


def create_dummy_analysis(video_path):
    """Create dummy analysis data"""
    return {
        "video_path": str(video_path),
        "analysis_timestamp": datetime.now().isoformat(),
        "duration_seconds": 150,
        "models_used": ["Placenta Detector (DEMO)", "Waste Classifier (DEMO)"],
        "waste_detected": {
            "bio_medical": 15.0,
            "sharps": 3.0,
            "pharmaceutical": 2.0,
            "placenta": 5.0,
            "general": 10.0
        },
        "confidence_scores": {
            "placenta_detection": 0.94,
            "waste_classification": 0.91
        },
        "violations": [
            {
                "type": "waste_mixing",
                "timestamp": "00:45",
                "description": "Bio-medical waste mixed with general waste",
                "severity": "high"
            }
        ]
    }


@app.get("/api/traces/waste")
async def get_waste_traces(limit: int = 50):
    """Get traces for waste agent"""
    traces = agent_traces.get("waste", [])
    return {
        "agent_id": "waste",
        "agent_name": "Waste Management Agent",
        "total_traces": len(traces),
        "traces": traces[-limit:]
    }


@app.get("/api/chat/history/waste")
async def get_waste_history(user_id: str = "system"):
    """Get chat history for waste agent"""
    key = f"waste_{user_id}"
    history = chat_histories.get(key, [])
    return {
        "agent_id": "waste",
        "user_id": user_id,
        "messages": history
    }


# ===== Startup Event =====
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Waste Management Backend Starting...")

    if AGENTS_AVAILABLE:
        print("✅ Waste agent loaded")
    else:
        print("❌ Waste agent not available")

    print("📡 Server ready at http://localhost:8000")
    print("📚 API Docs at http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)