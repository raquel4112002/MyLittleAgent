#!/usr/bin/env python3
"""Query the local FAISS-backed retrieval index for the red-team RAG layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import List

import faiss
import numpy as np

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

DEFAULT_DIM = 256


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


def openai_embed(text: str, model: str, base_url: str | None, api_key: str | None) -> np.ndarray:
    if OpenAI is None:
        raise RuntimeError("openai package is not available")
    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.embeddings.create(model=model, input=[text])
    vec = np.array(response.data[0].embedding, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def main() -> None:
    parser = argparse.ArgumentParser(description="Query a FAISS index for the red-team RAG layer")
    parser.add_argument("--index", required=True, help="Path to index directory")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--mode", choices=["hash", "openai"], default="hash")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL"))
    parser.add_argument("--api-key", default=os.environ.get("API_KEY"))
    args = parser.parse_args()

    index_dir = Path(args.index)
    metadata = json.loads((index_dir / "metadata.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(index_dir / "faiss.index"))

    if args.mode == "hash":
        q = hash_embed(args.query, dim=index.d).reshape(1, -1)
    else:
        q = openai_embed(args.query, args.embedding_model, args.base_url, args.api_key).reshape(1, -1)

    scores, ids = index.search(q, args.top_k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0:
            continue
        item = metadata[idx]
        results.append(
            {
                "score": float(score),
                "chunk_id": item["chunk_id"],
                "source_path": item["source_path"],
                "title": item["title"],
                "category": item["category"],
                "text": item["text"],
            }
        )

    print(json.dumps({"query": args.query, "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
