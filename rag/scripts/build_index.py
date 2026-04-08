#!/usr/bin/env python3
"""Build a local FAISS-backed retrieval index for the red-team RAG layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Any

import faiss
import numpy as np

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


TEXT_EXTENSIONS = {".md", ".txt", ".json"}
DEFAULT_DIM = 256


@dataclass
class ChunkRecord:
    chunk_id: str
    source_path: str
    title: str
    category: str
    text: str


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_documents(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def hash_embed(text: str, dim: int = DEFAULT_DIM) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float32)
    tokens = text.lower().split()
    if not tokens:
        return vec
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % dim
        sign = 1.0 if (h[4] % 2 == 0) else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def openai_embed_texts(texts: List[str], model: str, base_url: str | None, api_key: str | None) -> np.ndarray:
    if OpenAI is None:
        raise RuntimeError("openai package is not available")
    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.embeddings.create(model=model, input=texts)
    vectors = [np.array(item.embedding, dtype=np.float32) for item in response.data]
    matrix = np.vstack(vectors)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_chunk_records(root: Path, chunk_size: int, overlap: int) -> List[ChunkRecord]:
    records: List[ChunkRecord] = []
    for path in iter_documents(root):
        rel = path.relative_to(root)
        title = path.stem
        category = rel.parts[0] if len(rel.parts) > 1 else "misc"
        text = read_text_file(path)
        for idx, chunk in enumerate(chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
            chunk_id = f"{rel.as_posix()}::chunk_{idx}"
            records.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    source_path=rel.as_posix(),
                    title=title,
                    category=category,
                    text=chunk,
                )
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a FAISS index for the red-team RAG layer")
    parser.add_argument("--root", required=True, help="Path to rag data root")
    parser.add_argument("--out", required=True, help="Path to output index directory")
    parser.add_argument("--mode", choices=["hash", "openai"], default="hash", help="Embedding mode")
    parser.add_argument("--embedding-model", default="text-embedding-3-small", help="OpenAI-compatible embedding model")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL"), help="Embedding base URL")
    parser.add_argument("--api-key", default=os.environ.get("API_KEY"), help="Embedding API key")
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=150)
    args = parser.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    records = build_chunk_records(root, args.chunk_size, args.overlap)
    if not records:
        raise SystemExit("No documents found to index.")

    texts = [r.text for r in records]
    if args.mode == "hash":
        matrix = np.vstack([hash_embed(t) for t in texts])
    else:
        matrix = openai_embed_texts(texts, args.embedding_model, args.base_url, args.api_key)

    dim = matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)

    faiss.write_index(index, str(out / "faiss.index"))
    (out / "metadata.json").write_text(json.dumps([asdict(r) for r in records], indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "build_info.json").write_text(
        json.dumps(
            {
                "mode": args.mode,
                "embedding_model": args.embedding_model if args.mode == "openai" else None,
                "dimension": dim,
                "document_count": len(records),
                "chunk_size": args.chunk_size,
                "overlap": args.overlap,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Indexed {len(records)} chunks into {out}")


if __name__ == "__main__":
    main()
