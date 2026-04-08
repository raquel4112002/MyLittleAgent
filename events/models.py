from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(StrEnum):
    SESSION_CREATED = "session_created"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    LOG_LINE = "log_line"


class EventRecord(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    payload: Dict[str, Any] = Field(default_factory=dict)
