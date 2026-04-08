from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from entity.messages import Message


class SessionMessageStore:
    def __init__(self, root: Path | str = "sessions") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        path = self.root / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _messages_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "messages.jsonl"

    def append_message(self, session_id: str, sender_type: str, sender_id: str, message: Message) -> None:
        path = self._messages_file(session_id)
        payload = {
            "sender_type": sender_type,
            "sender_id": sender_id,
            "message": message.to_dict(include_data=False),
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def list_messages(self, session_id: str, limit: Optional[int] = None) -> List[dict]:
        path = self._messages_file(session_id)
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        if limit is not None:
            lines = lines[-limit:]
        results: List[dict] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            results.append(json.loads(line))
        return results
