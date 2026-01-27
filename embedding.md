# Embedding Layer Specification (Production)

## Goal
Implement a deterministic, production-ready embedding layer for a RAG pipeline.

This layer converts text chunks into vector embeddings and attaches metadata payloads,
without altering chunking logic or content.

---

## Model (LOCKED)
- Provider: OpenRouter
- Model: openai/text-embedding-3-large
- Dimensions: 3072
- Endpoint: https://openrouter.ai/api/v1/embeddings
- API: OpenAI-compatible

---

## Input
Each chunk is a dict with:
- chunk_id
- text
- metadata fields

---

## Embedding Rule
ONLY embed:
- chunk.text

NEVER embed metadata fields.

---

## Output Record Format
Each chunk becomes:

```json
{
  "id": "chunk_id",
  "vector": [float x 3072],
  "payload": {
    "doc_id": "...",
    "document_name": "...",
    "chunk_index": 12,
    "chunk_size": 842,
    "page_numbers": [82],
    "char_range": [220796, 221888],
    "section_hint": "Audit Committee",
    "strategy": "semantic_percentile",
    "source": "upload",
    "file_hash": "...",
    "ingestion_timestamp": "..."
  }
}
Batching
batch_size = 64

Retry on failure with exponential backoff

Log latency per batch

Hard fail if embedding fails (no random fallback)

Caching (MANDATORY)
Cache key:

scss
Copier le code
sha256(text + model_name)
Store vectors as:

bash
Copier le code
storage/embedding_cache/<hash>.npy
If cache exists, reuse vector.

Storage
Save final embeddings to:

pgsql
Copier le code
storage/embeddings/<doc_id>.json
JSON format only (no pickle).

Logging
Log:

number of chunks

total embedding time

avg time per batch

cache hits

cache misses

Errors
Never return random vectors

Never silently ignore errors

Fail fast and log clearly

Non-Goals
No chunking logic

No vector database insertion

No retrieval

No reranking

No metadata embedding