from __future__ import annotations

from events.models import EventRecord, EventType


def _get_event_bus():
    from server.state import get_event_bus
    return get_event_bus()


def _get_session_manager():
    from server.state import get_session_manager
    return get_session_manager()


def emit_log_line(session_id: str, source: str, message: str, details: dict | None = None) -> None:
    if not session_id:
        return
    _get_event_bus().emit(EventRecord(
        session_id=session_id,
        type=EventType.LOG_LINE,
        source=source,
        payload={"message": message, "details": details or {}},
    ))


def record_agent_message(session_id: str, agent_id: str, message) -> None:
    if not session_id:
        return
    _get_session_manager().record_agent_message(session_id, agent_id, message)
