from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PendingHumanAnswer:
    session_id: str
    request_id: str
    node_id: str
    task_description: str
    inputs: str | None = None
    response_text: str | None = None
    response_metadata: dict | None = None


class HumanResponseBroker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: Dict[str, PendingHumanAnswer] = {}
        self._events: Dict[str, threading.Event] = {}

    def register_request(self, session_id: str, request_id: str, node_id: str, task_description: str, inputs: str | None = None) -> PendingHumanAnswer:
        pending = PendingHumanAnswer(
            session_id=session_id,
            request_id=request_id,
            node_id=node_id,
            task_description=task_description,
            inputs=inputs,
        )
        with self._lock:
            self._pending[session_id] = pending
            self._events[session_id] = threading.Event()
        return pending

    def wait_for_response(self, session_id: str, timeout: float | None = None) -> Optional[PendingHumanAnswer]:
        with self._lock:
            event = self._events.get(session_id)
        if event is None:
            return None
        ok = event.wait(timeout=timeout)
        if not ok:
            return None
        with self._lock:
            pending = self._pending.pop(session_id, None)
            self._events.pop(session_id, None)
        return pending

    def submit_response(self, session_id: str, text: str, metadata: dict | None = None) -> bool:
        with self._lock:
            pending = self._pending.get(session_id)
            event = self._events.get(session_id)
            if pending is None or event is None:
                return False
            pending.response_text = text
            pending.response_metadata = metadata or {}
            event.set()
            return True

    def has_pending(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._pending
