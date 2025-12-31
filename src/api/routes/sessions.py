"""Session API Routes - CRUD for voice sessions.

Provides REST endpoints for session management:
- Create session
- Get session status
- Delete session
- WebRTC signaling

Reference: Implementation-v3.0.md §4.4
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.orchestrator.session import Session, SessionConfig, SessionManager
from src.llm import create_llm_client, build_messages
from src.api.webrtc.gateway import WebRTCGateway, create_webrtc_gateway
from src.api.websocket.blendshapes import get_blendshape_manager
from src.api.auth import verify_api_key

# All session routes require authentication
router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(verify_api_key)],
)

# Global managers (initialized on startup)
_session_manager: SessionManager | None = None
_webrtc_gateway: WebRTCGateway | None = None
_llm_client = None  # VLLMClient or MockLLMClient


def get_session_manager() -> SessionManager:
    """Get global session manager."""
    global _session_manager
    if _session_manager is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _session_manager = SessionManager(max_sessions=settings.max_concurrent_sessions)
    return _session_manager


def get_webrtc_gateway() -> WebRTCGateway:
    """Get global WebRTC gateway."""
    global _webrtc_gateway
    if _webrtc_gateway is None:
        _webrtc_gateway = create_webrtc_gateway()
    return _webrtc_gateway


async def get_llm_client():
    """Get global LLM client (VLLMClient or MockLLMClient based on settings)."""
    global _llm_client
    if _llm_client is None:
        _llm_client = await create_llm_client()
    return _llm_client


# Request/Response models
class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    session_id: str | None = Field(
        None,
        description="Optional session ID (generated if not provided)",
    )
    system_prompt: str = Field(
        "You are a helpful voice assistant.",
        description="System prompt for the LLM",
    )
    enable_avatar: bool = Field(
        True,
        description="Enable avatar animation output",
    )


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: str
    state: str
    message: str


class SessionStatusResponse(BaseModel):
    """Session status response."""

    session_id: str
    state: str
    is_running: bool
    context_tokens: int
    turns_completed: int
    avg_ttfa_ms: float


class WebRTCOfferRequest(BaseModel):
    """WebRTC SDP offer from client."""

    sdp: str = Field(..., description="SDP offer string")


class WebRTCAnswerResponse(BaseModel):
    """WebRTC SDP answer for client."""

    sdp: str = Field(..., description="SDP answer string")
    session_id: str


class ICECandidateRequest(BaseModel):
    """ICE candidate from client."""

    candidate: dict


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str = Field(..., description="User message text")
    stream: bool = Field(False, description="Stream response tokens")


class ChatResponse(BaseModel):
    """Chat message response."""

    response: str
    session_id: str


# Endpoints
@router.post("", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """Create a new voice session.

    Returns session_id and initial state.
    """
    manager = get_session_manager()

    # Check capacity
    if manager.available_slots <= 0:
        raise HTTPException(
            status_code=503,
            detail="No session slots available",
        )

    # Create session config
    config = SessionConfig(
        system_prompt=request.system_prompt,
        enable_avatar=request.enable_avatar,
    )

    # Create session
    session = await manager.create_session(
        session_id=request.session_id,
        config=config,
    )

    if session is None:
        raise HTTPException(
            status_code=503,
            detail="Failed to create session",
        )

    return CreateSessionResponse(
        session_id=session.session_id,
        state=session.state.value,
        message="Session created successfully",
    )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    """Get status of a session."""
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
        )

    return SessionStatusResponse(
        session_id=session.session_id,
        state=session.state.value,
        is_running=session.is_running,
        context_tokens=session.context_tokens,
        turns_completed=session.metrics.turns_completed,
        avg_ttfa_ms=session.metrics.avg_ttfa_ms,
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """End and delete a session."""
    manager = get_session_manager()

    success = await manager.end_session(session_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
        )

    # Also close WebRTC connection if exists
    gateway = get_webrtc_gateway()
    await gateway.close_connection(session_id)

    # Close blendshape WebSocket if exists
    blendshape_manager = get_blendshape_manager()
    await blendshape_manager.disconnect(session_id)

    return {"message": f"Session {session_id} ended"}


@router.get("")
async def list_sessions() -> dict:
    """List all active sessions."""
    manager = get_session_manager()
    return {
        "active_count": manager.active_count,
        "available_slots": manager.available_slots,
        "sessions": manager.list_sessions(),
    }


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest) -> ChatResponse:
    """Send a chat message and get LLM response.

    This is the main text interaction endpoint.
    For voice, use WebRTC audio streaming instead.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
        )

    try:
        llm = await get_llm_client()

        # Build messages with conversation history
        messages = build_messages(
            system_prompt=session.config.system_prompt,
            conversation=session.conversation_history,
            user_input=request.message,
        )

        # Generate response
        response = await llm.generate(messages)

        # Update session conversation history
        session.conversation_history.append({"role": "user", "content": request.message})
        session.conversation_history.append({"role": "assistant", "content": response.text})

        return ChatResponse(
            response=response.text,
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM generation failed: {str(e)}",
        )


# WebRTC signaling endpoints
@router.post("/{session_id}/offer", response_model=WebRTCAnswerResponse)
async def webrtc_offer(
    session_id: str,
    request: WebRTCOfferRequest,
) -> WebRTCAnswerResponse:
    """Handle WebRTC SDP offer and return answer.

    Client sends offer, server returns answer to establish
    WebRTC connection for audio and data channel.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
        )

    gateway = get_webrtc_gateway()

    try:
        answer_sdp = await gateway.handle_offer(session_id, request.sdp)
        return WebRTCAnswerResponse(
            sdp=answer_sdp,
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"WebRTC negotiation failed: {e}",
        )


@router.post("/{session_id}/ice-candidate")
async def ice_candidate(
    session_id: str,
    request: ICECandidateRequest,
) -> dict:
    """Add ICE candidate for WebRTC connection."""
    # Verify session exists
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
        )

    gateway = get_webrtc_gateway()

    try:
        await gateway.handle_ice_candidate(session_id, request.candidate)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add ICE candidate: {e}",
        )


# WebSocket endpoint for blendshapes (fallback when WebRTC data channel unavailable)
@router.websocket("/{session_id}/blendshapes")
async def blendshapes_websocket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket endpoint for blendshape streaming.

    Fallback for when WebRTC data channel is not available.
    Prefer WebRTC data channel to avoid TCP head-of-line blocking.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    blendshape_manager = get_blendshape_manager()

    try:
        handler = await blendshape_manager.connect(session_id, websocket)

        # Keep connection alive until disconnected
        while handler.is_connected:
            try:
                # Receive ping/pong or close
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    finally:
        await blendshape_manager.disconnect(session_id)
