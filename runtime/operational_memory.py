"""Operational memory helpers for workflow sessions.

This module provides a lightweight, file-backed operational memory layer for
workflow runs. It persists structured facts extracted from node outputs so
later agents/tools can retrieve prior observations from the same engagement.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


OPERATIONAL_MEMORY_FILENAME = "operational_memory.json"
ENGAGEMENT_SUMMARY_FILENAME = "engagement_summary.json"


@dataclass
class MemoryEntry:
    entry_type: str
    node_id: str
    source: str
    summary: str
    details: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OperationalMemoryStore:
    def __init__(self, workflow_dir: Path) -> None:
        self.workflow_dir = Path(workflow_dir)
        self.path = self.workflow_dir / OPERATIONAL_MEMORY_FILENAME
        self.summary_path = self.workflow_dir / ENGAGEMENT_SUMMARY_FILENAME

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"entries": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"entries": []}

    def save(self, payload: Dict[str, Any]) -> None:
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_summary(self, payload: Dict[str, Any]) -> None:
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def write_entries(self, entries: List[MemoryEntry]) -> Dict[str, Any]:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }
        self.save(payload)
        self.save_summary(build_engagement_summary(entries))
        return payload


def build_operational_memory_from_outputs(outputs: Dict[str, Any]) -> List[MemoryEntry]:
    entries: List[MemoryEntry] = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for node_id, payload in (outputs or {}).items():
        entry = _build_entry_for_node(node_id, payload, timestamp)
        if entry is not None:
            entries.append(entry)
    return entries


def build_engagement_summary(entries: List[MemoryEntry]) -> Dict[str, Any]:
    target_identifier = ""
    observations: List[str] = []
    findings: List[str] = []
    hypotheses: List[str] = []
    validation_steps: List[str] = []
    decisions: List[str] = []

    for entry in entries:
        details = entry.details or {}
        parsed = details.get("parsed") or {}
        if isinstance(parsed, dict) and not target_identifier:
            maybe_target = parsed.get("target_identifier")
            if isinstance(maybe_target, str) and maybe_target.strip():
                target_identifier = maybe_target.strip()

        summary = str(entry.summary or "").strip()
        if not summary:
            continue

        if entry.entry_type == "observation":
            _append_unique(observations, summary)
        elif entry.entry_type == "finding":
            _append_unique(findings, summary)
        elif entry.entry_type == "hypothesis":
            _append_unique(hypotheses, summary)
        elif entry.entry_type == "validation_step":
            _append_unique(validation_steps, summary)
        elif entry.entry_type == "decision":
            _append_unique(decisions, summary)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_identifier": target_identifier or None,
        "observations": observations[:5],
        "findings": findings[:5],
        "hypotheses": hypotheses[:5],
        "validation_steps": validation_steps[:5],
        "decisions": decisions[:5],
    }


def _append_unique(items: List[str], value: str) -> None:
    normalized = value.strip()
    if not normalized:
        return
    if normalized not in items:
        items.append(normalized)


def _build_entry_for_node(node_id: str, payload: Any, timestamp: str) -> Optional[MemoryEntry]:
    if not isinstance(payload, dict):
        return None

    results = payload.get("results") or []
    text_blobs: List[str] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        result_payload = result.get("payload") or {}
        content = result_payload.get("content")
        extracted = _extract_text(content)
        if extracted:
            text_blobs.append(extracted)

    if not text_blobs:
        return None

    merged = "\n\n".join(blob.strip() for blob in text_blobs if blob and blob.strip())
    if not merged.strip():
        return None

    details = _derive_structured_details(node_id, merged)
    summary = details.get("summary") or _truncate(merged, 220)
    entry_type = details.get("entry_type") or "note"

    return MemoryEntry(
        entry_type=entry_type,
        node_id=node_id,
        source=node_id,
        summary=summary,
        details=details,
        timestamp=timestamp,
    )


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    parts.append(str(item.get("text")))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part for part in parts if part)
    return ""


def _derive_structured_details(node_id: str, text: str) -> Dict[str, Any]:
    parsed = _safe_yaml_parse(text)
    details: Dict[str, Any] = {"raw_text": text}

    normalized_node = (node_id or "").lower()
    parsed_dict = parsed if isinstance(parsed, dict) else {}
    if parsed_dict:
        details["parsed"] = parsed_dict

    if "mission manager" in normalized_node:
        details["entry_type"] = "decision"
        details["summary"] = parsed_dict.get("mission_objective") or _truncate(text, 220)
    elif "context manager" in normalized_node:
        details["entry_type"] = "observation"
        details["summary"] = parsed_dict.get("current_phase") or _truncate(text, 220)
    elif "knowledge broker" in normalized_node:
        details["entry_type"] = "finding"
        details["summary"] = _summarize_broker_output(parsed_dict, text)
    elif "recon agent" in normalized_node:
        details["entry_type"] = "validation_step"
        details["summary"] = parsed_dict.get("recon_objective") or _truncate(text, 220)
    elif "surface vulnerability analyst" in normalized_node:
        details["entry_type"] = "finding"
        details["summary"] = parsed_dict.get("strongest_signal") or _truncate(text, 220)
    elif "attack path agent" in normalized_node:
        details["entry_type"] = "hypothesis"
        attack_path = parsed_dict.get("attack_path") if isinstance(parsed_dict.get("attack_path"), dict) else {}
        details["summary"] = attack_path.get("idea") or _truncate(text, 220)
    elif "execution planner" in normalized_node:
        details["entry_type"] = "validation_step"
        details["summary"] = parsed_dict.get("validation_goal") or _truncate(text, 220)
    elif "hallucination auditor" in normalized_node:
        details["entry_type"] = "finding"
        details["summary"] = parsed_dict.get("overall_assessment") or _truncate(text, 220)
    elif "revision coordinator" in normalized_node:
        details["entry_type"] = "decision"
        details["summary"] = str(parsed_dict.get("final_readiness")) if "final_readiness" in parsed_dict else _truncate(text, 220)
    elif "final synthesizer" in normalized_node:
        details["entry_type"] = "decision"
        details["summary"] = _truncate(text, 220)
    else:
        details["entry_type"] = "note"
        details["summary"] = _truncate(text, 220)

    return details


def _summarize_broker_output(parsed_dict: Dict[str, Any], text: str) -> str:
    if not parsed_dict:
        return _truncate(text, 220)

    op_mem = parsed_dict.get("operational_memory") or []
    if isinstance(op_mem, list):
        cleaned = []
        for item in op_mem:
            rendered = str(item).strip()
            lowered = rendered.lower()
            if not rendered:
                continue
            if "no operational memory" in lowered or "no prior-session memory" in lowered:
                continue
            cleaned.append(rendered)
        if cleaned:
            return _truncate(" | ".join(cleaned[:2]), 220)

    retrieval_goal = parsed_dict.get("retrieval_goal")
    if isinstance(retrieval_goal, str) and retrieval_goal.strip():
        return _truncate(retrieval_goal.strip(), 220)

    return _truncate(text, 220)


def _safe_yaml_parse(text: str) -> Any:
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def _truncate(text: str, limit: int) -> str:
    value = (text or "").strip().replace("\n", " ")
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"
