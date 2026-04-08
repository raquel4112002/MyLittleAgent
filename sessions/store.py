from __future__ import annotations

import json
from pathlib import Path
from typing import List

from sessions.models import SessionRecord


class SessionStore:
    def __init__(self, root: Path | str = "sessions") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        path = self.root / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _session_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "session.json"

    def create_session(self, record: SessionRecord) -> SessionRecord:
        self.save_session(record)
        return record

    def save_session(self, record: SessionRecord) -> SessionRecord:
        path = self._session_file(record.session_id)
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def load_session(self, session_id: str) -> SessionRecord | None:
        path = self._session_file(session_id)
        if not path.exists():
            return None
        return SessionRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def list_sessions(self) -> List[SessionRecord]:
        results: List[SessionRecord] = []
        for session_dir in sorted(self.root.iterdir() if self.root.exists() else [], reverse=True):
            if not session_dir.is_dir():
                continue
            session_file = session_dir / "session.json"
            if not session_file.exists():
                continue
            try:
                results.append(SessionRecord.model_validate(json.loads(session_file.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return results
