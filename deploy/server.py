"""
Google Ads API Agent — FastAPI Server
Exposes the agent as a REST API with conversation session management.

Run:
    uvicorn deploy.server:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    POST /chat              — Send a message, get a response
    POST /chat/stream       — Send a message, stream the response (SSE)
    POST /sessions          — Create a new conversation session
    DELETE /sessions/{id}   — Delete a session
    GET  /sessions/{id}     — Get session history
    GET  /health            — Health check
    GET  /tools             — List available tools
"""

import os
import uuid
import logging
import time
from collections import defaultdict
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from deploy.orchestrator import GoogleAdsAgent, create_agent_system

logger = logging.getLogger(__name__)

# ── Session Store ─────────────────────────────────────────────────────────────
sessions: Dict[str, GoogleAdsAgent] = {}

# ── Rate Limiting ─────────────────────────────────────────────────────────────
rate_limit_store: Dict[str, list] = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "30"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("Google Ads Agent server starting...")
    required_keys = ["ANTHROPIC_API_KEY"]
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        logger.error(f"Missing required env vars: {missing}")
    else:
        logger.info("Anthropic API key found")
    yield
    logger.info("Shutting down...")
    sessions.clear()


ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"
).split(",")

app = FastAPI(
    title="Google Ads Agent API",
    description="Enterprise Google Ads management powered by Claude",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiter per IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if t > now - RATE_LIMIT_WINDOW
    ]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Try again shortly."},
        )
    rate_limit_store[client_ip].append(now)
    return await call_next(request)


# ── Models ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls_made: int = 0

class SessionCreate(BaseModel):
    model: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    model: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_or_create_session(session_id: str = None, model: str = None) -> tuple:
    """Get existing session or create a new one."""
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]

    new_id = session_id or str(uuid.uuid4())
    agent = create_agent_system()
    if model:
        agent.model = model
    sessions[new_id] = agent
    return new_id, agent


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response. Auto-creates session if needed."""
    session_id, agent = get_or_create_session(request.session_id)

    try:
        history_before = len(agent.conversation_history)
        response_text = agent.chat(request.message)
        history_after = len(agent.conversation_history)

        # Count tool calls (each pair of assistant+user messages beyond the initial = 1 tool round)
        tool_calls = max(0, (history_after - history_before - 2) // 2)

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            tool_calls_made=tool_calls,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs.")


@app.post("/sessions", response_model=SessionInfo)
async def create_session(request: SessionCreate = None):
    """Create a new conversation session."""
    model = request.model if request else None
    session_id, agent = get_or_create_session(model=model)
    return SessionInfo(
        session_id=session_id,
        message_count=0,
        model=agent.model,
    )


@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session info."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    agent = sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        message_count=len(agent.conversation_history),
        model=agent.model,
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in sessions:
        del sessions[session_id]
    return {"deleted": session_id}


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "google_ads_configured": bool(os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")),
        "cloudinary_configured": bool(os.environ.get("CLOUDINARY_CLOUD_NAME")),
    }


@app.get("/tools")
async def list_tools():
    """List all available tools and their status."""
    from deploy.tool_executor import ToolExecutor
    executor = ToolExecutor()
    return {"tools": executor.list_available_tools()}
