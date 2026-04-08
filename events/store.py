from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from events.models import EventRecord


class EventStore:
    def __init__(self, root: Path | str = "sessions") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        path = self.root / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _events_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "events.jsonl"

    def append_event(self, session_id: str, event: EventRecord) -> None:
        path = self._events_file(session_id)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def list_events(self, session_id: str, limit: Optional[int] = None) -> List[EventRecord]:
        path = self._events_file(session_id)
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        if limit is not None:
            lines = lines[-limit:]
        results: List[EventRecord] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            results.append(EventRecord.model_validate(json.loads(line)))
        return results
