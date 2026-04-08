from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from entity.messages import Message, MessageRole
from events.models import EventRecord, EventType
from sessions.message_store import SessionMessageStore
from sessions.models import SessionRecord, SessionStatus
from sessions.store import SessionStore


def _get_event_bus():
    from server.state import get_event_bus
    return get_event_bus()


class SessionManager:
    def __init__(self, store: SessionStore | None = None, message_store: SessionMessageStore | None = None) -> None:
        self.store = store or SessionStore()
        self.message_store = message_store or SessionMessageStore()

    def create_session(self, workflow_id: str, metadata: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> SessionRecord:
        record = SessionRecord(
            session_id=session_id or SessionRecord().session_id,
            workflow_id=workflow_id,
            metadata=metadata or {},
        )
        self.store.create_session(record)
        _get_event_bus().emit(EventRecord(
            session_id=record.session_id,
            type=EventType.SESSION_CREATED,
            source="session_manager",
            payload={"workflow_id": workflow_id, "status": record.status},
        ))
        return record

    def get_session(self, session_id: str) -> SessionRecord | None:
        return self.store.load_session(session_id)

    def list_sessions(self):
        return self.store.list_sessions()

    def update_session(self, session_id: str, **fields) -> SessionRecord | None:
        record = self.store.load_session(session_id)
        if record is None:
            return None
        for key, value in fields.items():
            setattr(record, key, value)
        record.updated_at = datetime.now(timezone.utc)
        return self.store.save_session(record)

    def mark_running(self, session_id: str, workflow_id: Optional[str] = None) -> SessionRecord | None:
        record = self.update_session(session_id, status=SessionStatus.RUNNING)
        if record:
            _get_event_bus().emit(EventRecord(
                session_id=session_id,
                type=EventType.WORKFLOW_STARTED,
                source="session_manager",
                payload={"workflow_id": workflow_id or record.workflow_id},
            ))
        return record

    def mark_agent_active(self, session_id: str, agent_id: str, node_id: Optional[str] = None) -> SessionRecord | None:
        record = self.update_session(session_id, current_agent_id=agent_id, current_node_id=node_id or agent_id)
        if record:
            _get_event_bus().emit(EventRecord(
                session_id=session_id,
                type=EventType.AGENT_STARTED,
                source="graph_executor",
                payload={"agent_id": agent_id, "node_id": node_id or agent_id},
            ))
        return record

    def mark_agent_completed(self, session_id: str, agent_id: str, node_id: Optional[str] = None) -> SessionRecord | None:
        record = self.update_session(session_id, current_agent_id=agent_id, current_node_id=node_id or agent_id)
        if record:
            _get_event_bus().emit(EventRecord(
                session_id=session_id,
                type=EventType.AGENT_COMPLETED,
                source="graph_executor",
                payload={"agent_id": agent_id, "node_id": node_id or agent_id},
            ))
        return record

    def mark_completed(self, session_id: str) -> SessionRecord | None:
        record = self.update_session(session_id, status=SessionStatus.COMPLETED)
        if record:
            _get_event_bus().emit(EventRecord(
                session_id=session_id,
                type=EventType.WORKFLOW_COMPLETED,
                source="session_manager",
                payload={"workflow_id": record.workflow_id},
            ))
        return record

    def mark_failed(self, session_id: str, error: str) -> SessionRecord | None:
        record = self.update_session(session_id, status=SessionStatus.FAILED)
        if record:
            _get_event_bus().emit(EventRecord(
                session_id=session_id,
                type=EventType.WORKFLOW_FAILED,
                source="session_manager",
                payload={"workflow_id": record.workflow_id, "error": error},
            ))
        return record

    def record_agent_message(self, session_id: str, agent_id: str, message: Message) -> None:
        self.message_store.append_message(session_id, "agent", agent_id, message)
        _get_event_bus().emit(EventRecord(
            session_id=session_id,
            type=EventType.AGENT_MESSAGE,
            source=agent_id,
            payload={
                "agent_id": agent_id,
                "role": message.role.value,
                "text": message.text_content(),
                "metadata": dict(message.metadata),
            },
        ))

    def record_human_message(self, session_id: str, node_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        message = Message(role=MessageRole.USER, content=text, metadata=metadata or {})
        self.message_store.append_message(session_id, "human", node_id, message)
        _get_event_bus().emit(EventRecord(
            session_id=session_id,
            type=EventType.HUMAN_MESSAGE,
            source="human",
            payload={"node_id": node_id, "text": text, "metadata": metadata or {}},
        ))

    def mark_waiting_for_human(self, session_id: str, node_id: str, task_description: str, inputs: Optional[str] = None) -> SessionRecord | None:
        record = self.update_session(session_id, status=SessionStatus.WAITING_FOR_HUMAN, current_agent_id=node_id, current_node_id=node_id)
        if record:
            _get_event_bus().emit(EventRecord(
                session_id=session_id,
                type=EventType.AGENT_WAITING_FOR_HUMAN,
                source=node_id,
                payload={"node_id": node_id, "task_description": task_description, "inputs": inputs},
            ))
        return record
