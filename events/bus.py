from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict, Set

from events.models import EventRecord
from events.store import EventStore


class EventBus:
    def __init__(self, store: EventStore | None = None) -> None:
        self.store = store or EventStore()
        self._subscribers: DefaultDict[str, Set[asyncio.Queue]] = defaultdict(set)

    def emit(self, event: EventRecord) -> None:
        self.store.append_event(event.session_id, event)
        for queue in list(self._subscribers.get(event.session_id, set())):
            try:
                queue.put_nowait(event)
            except Exception:
                pass

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[session_id].add(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(session_id)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(session_id, None)
