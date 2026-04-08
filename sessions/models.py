from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    RESUMING = "RESUMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SessionRecord(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_node_id: Optional[str] = None
    current_agent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
