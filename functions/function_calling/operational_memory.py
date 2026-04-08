import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Tuple

import yaml

from utils.function_catalog import ParamMeta


DEFAULT_MEMORY_FILE = "operational_memory.json"
ENGAGEMENT_SUMMARY_FILE = "engagement_summary.json"


def retrieve_operational_context(
    task: Annotated[str, ParamMeta(description="Current task or decision need")],
    entry_types: Annotated[List[str], ParamMeta(description="Optional entry types to keep, e.g. observation,finding,hypothesis,decision,validation_step")] = [],
    limit: Annotated[int, ParamMeta(description="Maximum number of memory items to return")] = 5,
    target_identifier: Annotated[str, ParamMeta(description="Optional target identifier used to search prior sessions")] = "",
    include_prior_sessions: Annotated[bool, ParamMeta(description="Whether to include memory from prior sessions for the same target")] = True,
    compact: Annotated[bool, ParamMeta(description="Return engagement summaries instead of raw entries when possible")] = True,
    _context: Dict[str, Any] | None = None,
) -> str:
    """Retrieve compact operational memory from the current workflow session and, optionally, prior related sessions."""
    graph_directory = None
    if _context:
        graph_directory = _context.get("graph_directory")

    if not graph_directory:
        raise RuntimeError("graph_directory missing from tool context")

    graph_dir = Path(graph_directory)
    current_memory_path = graph_dir / DEFAULT_MEMORY_FILE
    current_payload = _load_json(current_memory_path)
    current_entries = list((current_payload or {}).get("entries") or [])

    inferred_target = target_identifier.strip() or _infer_target_identifier(current_entries)
    related_sessions: List[Dict[str, Any]] = []
    prior_entries: List[Dict[str, Any]] = []
    prior_summaries: List[Dict[str, Any]] = []

    effective_include_prior = include_prior_sessions or bool(inferred_target)
    if effective_include_prior:
        prior_entries, prior_summaries, related_sessions = _collect_prior_session_entries(graph_dir, inferred_target)

    combined = []
    for entry in current_entries:
        enriched = dict(entry)
        enriched.setdefault("memory_scope", "current_session")
        if _is_useful_entry(enriched):
            combined.append(enriched)
    for entry in prior_entries:
        enriched = dict(entry)
        enriched.setdefault("memory_scope", "prior_session")
        if _is_useful_entry(enriched):
            combined.append(enriched)

    allowed = {value.strip().lower() for value in entry_types if str(value).strip()}
    if allowed:
        combined = [entry for entry in combined if str(entry.get("entry_type", "")).lower() in allowed]

    ranked = sorted(combined, key=lambda entry: _score_entry(entry, task), reverse=True)
    selected = ranked[: max(1, limit)]

    response: Dict[str, Any] = {
        "task": task,
        "memory_available": bool(combined),
        "target_identifier": inferred_target or None,
        "note": _build_note(bool(current_entries), bool(prior_entries), inferred_target),
    }

    if compact:
        response["memory_counts"] = {
            "current_session": len(current_entries),
            "prior_sessions": len(prior_entries),
            "related_session_count": len(related_sessions),
        }
        response["engagement_summary"] = _build_compact_summary(graph_dir, prior_summaries, selected)
        response["selected_entries"] = _minify_entries(selected[:2])
    else:
        response["current_session_entry_count"] = len(current_entries)
        response["prior_session_entry_count"] = len(prior_entries)
        response["related_sessions"] = related_sessions
        response["selected_entries"] = selected

    return json.dumps(response, indent=2, ensure_ascii=False)


def _collect_prior_session_entries(graph_dir: Path, target_identifier: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not target_identifier:
        return [], [], []

    current_session_name = graph_dir.name
    warehouse_root = graph_dir.parent
    if not warehouse_root.exists():
        return [], [], []

    related_entries: List[Dict[str, Any]] = []
    related_summaries: List[Dict[str, Any]] = []
    related_sessions: List[Dict[str, Any]] = []

    for session_dir in sorted(warehouse_root.glob("session_*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if session_dir.name == current_session_name:
            continue

        summary = _load_yaml(session_dir / "workflow_summary.yaml")
        if not isinstance(summary, dict):
            continue
        design_path = str(summary.get("design_path") or "")
        if "redteam_phase5_memory_v1.yaml" not in design_path:
            continue

        memory_payload = _load_json(session_dir / DEFAULT_MEMORY_FILE)
        entries = list((memory_payload or {}).get("entries") or [])
        if not entries:
            continue

        session_target = _infer_target_identifier(entries)
        if not _same_target(target_identifier, session_target):
            continue

        engagement_summary = _load_json(session_dir / ENGAGEMENT_SUMMARY_FILE) or {}
        if engagement_summary:
            engagement_summary = dict(engagement_summary)
            engagement_summary["source_session"] = session_dir.name
            related_summaries.append(engagement_summary)

        related_sessions.append(
            {
                "session": session_dir.name,
                "target_identifier": session_target,
                "entry_count": len(entries),
            }
        )
        for entry in entries:
            enriched = dict(entry)
            enriched["source_session"] = session_dir.name
            related_entries.append(enriched)

    return related_entries, related_summaries, related_sessions


def _build_compact_summary(
    graph_dir: Path,
    prior_summaries: List[Dict[str, Any]],
    selected_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    current_summary = _load_json(graph_dir / ENGAGEMENT_SUMMARY_FILE) or {}
    useful_prior_summaries = [item for item in prior_summaries if _summary_has_signal(item)]
    useful_top_points = [item for item in selected_entries if _entry_has_signal(item)]
    return {
        "current_session": _trim_summary(current_summary),
        "prior_sessions": [_trim_summary(item) for item in useful_prior_summaries[:2]],
        "top_memory_points": [
            {
                "type": item.get("entry_type"),
                "summary": item.get("summary"),
                "source_session": item.get("source_session"),
                "memory_scope": item.get("memory_scope"),
                "node_id": item.get("node_id"),
            }
            for item in useful_top_points[:2]
        ],
    }


def _trim_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(summary, dict):
        return {}
    trimmed = {
        "source_session": summary.get("source_session"),
        "target_identifier": summary.get("target_identifier"),
        "observations": _clean_summary_values(summary.get("observations") or [])[:2],
        "findings": _clean_summary_values(summary.get("findings") or [])[:2],
        "hypotheses": _clean_summary_values(summary.get("hypotheses") or [])[:2],
        "validation_steps": _clean_summary_values(summary.get("validation_steps") or [])[:2],
        "decisions": _clean_summary_values(summary.get("decisions") or [])[:2],
    }
    return {k: v for k, v in trimmed.items() if v not in (None, [], "")}


def _clean_summary_values(values: List[Any]) -> List[str]:
    cleaned: List[str] = []
    for value in values:
        text = str(value).strip()
        lowered = text.lower()
        if not text:
            continue
        if "retrieval_goal:" in lowered or "operational_memory:" in lowered:
            continue
        if text in {"Validation & Payload Execution", "Initial Attack Path Hypothesis"}:
            continue
        cleaned.append(text)
    return cleaned


def _minify_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "entry_type": entry.get("entry_type"),
            "summary": entry.get("summary"),
            "source_session": entry.get("source_session"),
            "memory_scope": entry.get("memory_scope"),
            "node_id": entry.get("node_id"),
        }
        for entry in entries
        if _entry_has_signal(entry)
    ]


def _infer_target_identifier(entries: List[Dict[str, Any]]) -> str:
    for entry in entries:
        details = entry.get("details") or {}
        parsed = details.get("parsed") or {}
        if isinstance(parsed, dict):
            value = parsed.get("target_identifier")
            if isinstance(value, str) and value.strip():
                return value.strip()
        raw_text = str(details.get("raw_text") or "")
        marker = "target_identifier:"
        if marker in raw_text:
            tail = raw_text.split(marker, 1)[1].splitlines()[0].strip()
            if tail:
                return tail
        if "Target URL:" in raw_text:
            tail = raw_text.split("Target URL:", 1)[1].splitlines()[0].strip()
            if tail:
                return tail
    return ""


def _same_target(left: str, right: str) -> bool:
    return _normalize_target(left) == _normalize_target(right) if left and right else False


def _normalize_target(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def _build_note(has_current: bool, has_prior: bool, target_identifier: str) -> str:
    if has_current and has_prior:
        return f"Using current-session memory plus prior-session memory for target {target_identifier}."
    if has_current:
        return "Using current-session operational memory only."
    if has_prior:
        return f"No current-session memory yet; using prior-session memory for target {target_identifier}."
    return "No operational memory found for current or prior related sessions."


def _load_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_yaml(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _is_useful_entry(entry: Dict[str, Any]) -> bool:
    summary = str(entry.get("summary", "")).lower()
    details = json.dumps(entry.get("details") or {}, ensure_ascii=False).lower()
    noisy_markers = [
        "no operational memory file found",
        "no prior session observations available",
        "no prior operational memory available",
        "session cannot leverage historical observations",
        "planning must proceed without memory-derived facts",
    ]
    if any(marker in summary or marker in details for marker in noisy_markers):
        return False
    if "knowledge broker" in str(entry.get("node_id", "")).lower() and (
        "retrieval_goal:" in summary or "operational_memory:" in summary
    ):
        return False
    return True


def _entry_has_signal(entry: Dict[str, Any]) -> bool:
    if not _is_useful_entry(entry):
        return False
    summary = str(entry.get("summary", "")).strip()
    return len(summary) >= 12


def _summary_has_signal(summary: Dict[str, Any]) -> bool:
    if not isinstance(summary, dict):
        return False
    for key in ("observations", "findings", "hypotheses", "validation_steps", "decisions"):
        values = _clean_summary_values(list(summary.get(key) or []))
        if any(str(v).strip() for v in values):
            return True
    return False


def _score_entry(entry: Dict[str, Any], task: str) -> int:
    haystack_parts = [
        str(entry.get("entry_type", "")),
        str(entry.get("node_id", "")),
        str(entry.get("summary", "")),
        json.dumps(entry.get("details") or {}, ensure_ascii=False),
    ]
    haystack = " ".join(haystack_parts).lower()
    score = 0
    for token in _tokenize(task):
        if token in haystack:
            score += 3
    entry_type = str(entry.get("entry_type", "")).lower()
    if entry_type == "hypothesis":
        score += 5
    elif entry_type == "finding":
        score += 4
    elif entry_type == "validation_step":
        score += 3
    elif entry_type == "observation":
        score += 2
    elif entry_type == "decision":
        score += 1
    if entry.get("memory_scope") == "current_session":
        score += 2
    if str(entry.get("source_session", "")):
        score += 1
    node_id = str(entry.get("node_id", "")).lower()
    if "recon agent" in node_id:
        score += 4
    elif "attack path agent" in node_id:
        score += 4
    elif "surface vulnerability analyst" in node_id:
        score += 3
    elif "execution planner" in node_id:
        score += 3
    elif "context manager" in node_id:
        score -= 4
    elif "mission manager" in node_id:
        score -= 3
    elif "knowledge broker" in node_id:
        score -= 6
    if "contact" in haystack:
        score += 2
    if "xss" in haystack or "csrf" in haystack or "input validation" in haystack:
        score += 2
    if "file upload" in haystack or "cwe-434" in haystack:
        score -= 4
    return score


def _tokenize(value: str) -> List[str]:
    raw = (value or "").lower().replace("\n", " ")
    tokens = [token.strip(" ,.;:()[]{}") for token in raw.split()]
    return [token for token in tokens if len(token) >= 3]
