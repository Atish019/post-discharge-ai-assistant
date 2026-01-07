"""
FastAPI application for Post-Discharge Medical AI Assistant.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict
import uuid
from datetime import datetime

from src.orchestration.multi_agent_graph import process_message
from src.utils.logger import log_system

# Initialize FastAPI
app = FastAPI(
    title="Post-Discharge Medical AI Assistant",
    description="Educational AI assistant with LangGraph orchestration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Sessions
sessions: Dict[str, Dict] = {}

# Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    method: str
    answer: str
    patient_identified: bool = False
    timestamp: str

# Session Management
def get_session(session_id: Optional[str] = None) -> Dict:
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    new_session_id = session_id or str(uuid.uuid4())
    sessions[new_session_id] = {
        "id": new_session_id,
        "patient_data": None,
        "created_at": datetime.now().isoformat(),
        "message_count": 0
    }
    
    log_system(f"New session created: {new_session_id}")
    return sessions[new_session_id]

# Events
@app.on_event("startup")
async def startup_event():
    log_system("=" * 60)
    log_system(" Post-Discharge Medical AI Assistant Started")
    log_system(" LangGraph Multi-Agent Orchestration Enabled")
    log_system("=" * 60)
    log_system("Frontend: http://localhost:8000/app")
    log_system("API Docs: http://localhost:8000/docs")
    log_system("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    log_system("=" * 60)
    log_system(" Application shutting down")
    log_system(f"Total sessions: {len(sessions)}")
    log_system("=" * 60)

# Endpoints
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/app")
async def serve_app():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "orchestration": "LangGraph",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session = get_session(request.session_id)
        
        log_system(f"[Session: {session['id']}] User: {request.message}")
        
        # Process through LangGraph
        response = process_message(request.message, session)
        
        # Update session
        session["patient_data"] = response["patient_data"]
        session["message_count"] = response["message_count"]
        
        return ChatResponse(
            session_id=session["id"],
            method=response["method"],
            answer=response["answer"],
            patient_identified=response["patient_identified"],
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        log_system(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        log_system(f"Session deleted: {session_id}")
        return {"message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")