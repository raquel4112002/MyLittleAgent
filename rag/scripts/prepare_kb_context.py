#!/usr/bin/env python3
"""Prepare compact retrieval context for the Knowledge Broker from the local RAG index."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


def is_bad_windows_alias(path_str: str | None) -> bool:
    if not path_str:
        return False
    normalized = path_str.replace("/", "\\").lower()
    return "\\windowsapps\\python" in normalized


def resolve_python_candidates() -> List[List[str]]:
    candidates: List[List[str]] = []

    if sys.executable and not is_bad_windows_alias(sys.executable):
        candidates.append([sys.executable])

    for name in ("python", "python3"):
        found = shutil.which(name)
        if found and not is_bad_windows_alias(found):
            candidates.append([found])

    if os.name == "nt":
        py_launcher = shutil.which("py")
        if py_launcher:
            candidates.append([py_launcher, "-3"])
            candidates.append([py_launcher])

    unique: List[List[str]] = []
    seen = set()
    for candidate in candidates:
        key = tuple(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def run_query(index_dir: Path, query: str, top_k: int, mode: str) -> Dict[str, Any]:
    candidates = resolve_python_candidates()
    if not candidates:
        raise RuntimeError("No usable Python interpreter found for nested RAG query")

    base_args = [
        str(Path(__file__).with_name("query_index.py")),
        "--index",
        str(index_dir),
        "--query",
        query,
        "--top-k",
        str(top_k),
        "--mode",
        mode,
    ]

    last_error = None
    for candidate in candidates:
        cmd = candidate + base_args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            details = stderr or stdout or str(exc)
            last_error = RuntimeError(f"candidate={candidate} details={details}")
            continue
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Nested RAG query failed for all Python interpreter candidates: {last_error}")


def build_queries(task: str, target_type: str | None = None, target_identifier: str | None = None) -> List[str]:
    queries = [task.strip()]
    if target_type:
        queries.append(f"{target_type} reconnaissance and attack path validation")
    if target_identifier:
        queries.append(f"web application testing planning for target {target_identifier}")
    return [q for q in queries if q]


def dedupe_results(results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    seen = set()
    final = []
    for item in results:
        key = item.get("chunk_id")
        if key in seen:
            continue
        seen.add(key)
        final.append(item)
        if len(final) >= limit:
            break
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Knowledge Broker retrieval context")
    parser.add_argument("--index", required=True, help="Path to rag/index")
    parser.add_argument("--task", required=True, help="Mission/task description")
    parser.add_argument("--target-type", default=None)
    parser.add_argument("--target-identifier", default=None)
    parser.add_argument("--mode", default="hash", choices=["hash", "openai"])
    parser.add_argument("--top-k-per-query", type=int, default=3)
    parser.add_argument("--final-limit", type=int, default=5)
    parser.add_argument("--out", default=None, help="Optional output file path")
    args = parser.parse_args()

    index_dir = Path(args.index)
    queries = build_queries(args.task, args.target_type, args.target_identifier)

    all_results: List[Dict[str, Any]] = []
    for q in queries:
        payload = run_query(index_dir, q, args.top_k_per_query, args.mode)
        all_results.extend(payload.get("results", []))

    final_results = dedupe_results(all_results, args.final_limit)
    output = {
        "task": args.task,
        "target_type": args.target_type,
        "target_identifier": args.target_identifier,
        "queries": queries,
        "retrieved_context": [
            {
                "source_path": item.get("source_path"),
                "category": item.get("category"),
                "title": item.get("title"),
                "score": item.get("score"),
                "text": item.get("text"),
            }
            for item in final_results
        ],
    }

    serialized = json.dumps(output, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(serialized, encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
