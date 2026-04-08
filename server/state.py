"""Global state shared across server modules."""

from typing import Optional

from events.bus import EventBus
from server.services.websocket_manager import WebSocketManager
from sessions.manager import SessionManager
from utils.exceptions import ValidationError

websocket_manager: Optional[WebSocketManager] = None
session_manager: Optional[SessionManager] = None
event_bus: Optional[EventBus] = None


def init_state() -> None:
    """Ensure global singletons are ready for incoming requests."""

    get_websocket_manager()
    get_session_manager()
    get_event_bus()


def get_websocket_manager() -> WebSocketManager:
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager()
    return websocket_manager


def get_session_manager() -> SessionManager:
    global session_manager
    if session_manager is None:
        session_manager = SessionManager()
    return session_manager


def get_event_bus() -> EventBus:
    global event_bus
    if event_bus is None:
        event_bus = EventBus()
    return event_bus


def ensure_known_session(session_id: str, *, require_connection: bool = False) -> WebSocketManager:
    """Return the WebSocket manager if the session is connected or known."""

    manager = get_websocket_manager()
    if not session_id:
        raise ValidationError("Session not connected", details={"session_id": session_id})

    if session_id in manager.active_connections:
        return manager

    if not require_connection and manager.session_store.has_session(session_id):
        return manager

    raise ValidationError("Session not connected", details={"session_id": session_id})
