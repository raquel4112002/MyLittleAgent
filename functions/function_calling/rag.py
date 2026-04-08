import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Dict, Any, List

from utils.function_catalog import ParamMeta


def retrieve_rag_context(
    task: Annotated[str, ParamMeta(description="Mission or retrieval task description")],
    target_type: Annotated[str, ParamMeta(description="Target type, e.g. OWASP Juice Shop laboratory environment")] = "",
    target_identifier: Annotated[str, ParamMeta(description="Target URL, hostname, or other identifier")] = "",
    top_k_per_query: Annotated[int, ParamMeta(description="Top results per internal query")] = 3,
    final_limit: Annotated[int, ParamMeta(description="Maximum total retrieved chunks to return")] = 5,
    mode: Annotated[str, ParamMeta(description="Embedding mode: hash or openai")] = "hash",
    _context: Dict[str, Any] | None = None,
) -> str:
    """
    Retrieve compact RAG context from the local red-team knowledge index.
    Returns JSON text that can be interpreted by the Knowledge Broker.
    """
    root = Path(__file__).resolve().parents[2]
    script = root / "rag" / "scripts" / "prepare_kb_context.py"
    index_dir = root / "rag" / "index"

    if not script.exists():
        raise FileNotFoundError(f"RAG prepare script not found: {script}")
    if not index_dir.exists():
        raise FileNotFoundError(f"RAG index directory not found: {index_dir}")

    def is_bad_windows_alias(path_str: str | None) -> bool:
        if not path_str:
            return False
        normalized = path_str.replace("/", "\\").lower()
        return "\\windowsapps\\python" in normalized

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

    unique_candidates: List[List[str]] = []
    seen = set()
    for candidate in candidates:
        key = tuple(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(candidate)

    if not unique_candidates:
        raise RuntimeError("No usable Python interpreter found for RAG retrieval tool")

    base_args = [
        str(script),
        "--index",
        str(index_dir),
        "--task",
        task,
        "--mode",
        mode,
        "--top-k-per-query",
        str(top_k_per_query),
        "--final-limit",
        str(final_limit),
    ]

    if target_type:
        base_args.extend(["--target-type", target_type])
    if target_identifier:
        base_args.extend(["--target-identifier", target_identifier])

    last_error = None
    for candidate in unique_candidates:
        cmd = candidate + base_args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            payload = json.loads(result.stdout)
            return json.dumps(payload, indent=2, ensure_ascii=False)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or '').strip()
            stdout = (exc.stdout or '').strip()
            details = stderr or stdout or str(exc)
            last_error = RuntimeError(f"candidate={candidate} details={details}")
            continue
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"RAG retrieval failed with all Python interpreter candidates: {last_error}")
