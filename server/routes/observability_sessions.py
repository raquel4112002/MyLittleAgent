from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.state import get_event_bus, get_session_manager

router = APIRouter()


class HumanReplyPayload(BaseModel):
    text: str
    metadata: Dict[str, Any] | None = None


@router.get("/api/observability/sessions")
async def list_observability_sessions():
    manager = get_session_manager()
    return [item.model_dump(mode="json") for item in manager.list_sessions()]


@router.get("/api/observability/sessions/{session_id}")
async def get_observability_session(session_id: str):
    manager = get_session_manager()
    session = manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump(mode="json")


@router.get("/api/observability/sessions/{session_id}/events")
async def get_observability_session_events(session_id: str, limit: int | None = None):
    events = get_event_bus().store.list_events(session_id, limit=limit)
    return [item.model_dump(mode="json") for item in events]


@router.get("/api/observability/sessions/{session_id}/messages")
async def get_observability_session_messages(session_id: str, limit: int | None = None):
    manager = get_session_manager()
    session = manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return manager.message_store.list_messages(session_id, limit=limit)


@router.post("/api/observability/sessions/{session_id}/reply")
async def reply_to_pending_human_request(session_id: str, payload: HumanReplyPayload):
    manager = get_session_manager()
    session = manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    updated = manager.answer_pending_request(session_id, payload.text, metadata=payload.metadata)
    if updated is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated.model_dump(mode="json")
