# RAG Layer for the Red-Team Thesis Framework

This directory contains the first practical implementation of the retrieval layer for the autonomous penetration-testing framework.

## Purpose

This RAG layer is intended to support the **Knowledge Broker** agent by providing grounded technical knowledge from curated security sources.

In this first implementation, the retrieval layer is intentionally simple and local:

- documents are stored under `rag/data/`
- documents are chunked into smaller passages
- chunk embeddings are generated
- embeddings are stored in a local FAISS index
- retrieval queries return top relevant chunks with metadata

## Directory structure

- `rag/data/`
  - input knowledge sources
- `rag/index/`
  - generated vector index and metadata
- `rag/scripts/build_index.py`
  - builds the local index
- `rag/scripts/query_index.py`
  - queries the local index
- `rag/scripts/prepare_kb_context.py`
  - prepares compact retrieval context for the Knowledge Broker

## Recommended initial sources

Suggested first knowledge sources:

- OWASP Testing Guide
- OWASP Top 10
- selected CWE entries
- selected MITRE ATT&CK techniques relevant to web applications
- documentation for tools such as nmap, ffuf, nuclei, sqlmap
- experimental notes and benchmark observations

## Example workflow

### 1. Add documents

Place `.md`, `.txt`, or `.json` files inside the folders under `rag/data/`.

### 2. Build the index

```bash
python rag/scripts/build_index.py --root rag/data --out rag/index
```

### 3. Query the index directly

```bash
python rag/scripts/query_index.py --index rag/index --query "file upload validation in web applications"
```

### 4. Prepare retrieval context for the Knowledge Broker

```bash
python rag/scripts/prepare_kb_context.py \
  --index rag/index \
  --task "Analyze a controlled web application target" \
  --target-type "OWASP Juice Shop laboratory environment" \
  --target-identifier "http://localhost:3000" \
  --out rag/index/kb_context.json
```

The output file can then be pasted or injected into the Knowledge Broker stage as retrieved context.

## Embeddings

This implementation supports two modes:

1. **hash mode**
   - fully local
   - no external model required
   - lower semantic quality
   - useful for infrastructure bring-up and debugging

2. **openai-compatible embedding mode**
   - uses an OpenAI-compatible embeddings endpoint
   - suitable for Ollama-compatible or other API-based embeddings if configured

The mode is selected through command-line arguments.

## Current scope

This is the first retrieval implementation for the thesis project.
It is not yet fully integrated into ChatDev tools or agent function-calling.
The immediate goal is to:

- build and validate the retrieval pipeline;
- test document quality and chunking strategy;
- evaluate retrieval usefulness for the Knowledge Broker;
- prepare later integration into Phase 3 workflows.
