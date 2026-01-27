1. Goal of This Layer

This layer is responsible for persistently storing embeddings with metadata in a way that is:

Deterministic

Idempotent

Production-grade

Fast

Filterable

Compatible with future retrievers

⚠️ No retrieval logic is implemented here yet
This layer is storage-only.

2. Technology Choice
Vector Database

Qdrant (local, Docker)

Why:

Real vector database (not a toy)

Stores vectors + payload together

Supports filtering natively

Fast HNSW indexing

Easy to move to cloud later

3. Connection Configuration
Local Qdrant
URL: http://localhost:6333
API KEY: None (local mode)

Python client
pip install qdrant-client

4. Collection Definition (MANDATORY)
Collection name
rag_chunks

Vector configuration
size = 3072
distance = "Cosine"


Reason:

Matches OpenAI text-embedding-3-large

Best semantic similarity metric

5. Data Model (STRICT CONTRACT)

Each chunk = 1 vector = 1 Qdrant point

5.1 Vector
vector: List[float]  # length = 3072

5.2 Point ID (CRITICAL)
point_id = chunk["chunk_id"]


Never use:

random UUIDs

array indexes

hashes

This guarantees:

upsert safety

re-ingestion

re-embedding

deduplication

5.3 Payload (Metadata)

Payload is flat JSON (no nesting).

{
  "doc_id": "uuid",
  "document_name": "file.pdf",
  "chunk_id": "uuid",
  "chunk_index": 0,
  "chunk_size": 843,
  "strategy": "semantic_percentile",
  "page_numbers": [12, 13],
  "char_start": 12033,
  "char_end": 12876,
  "section_hint": "Risk Committee",
  "source": "upload",
  "file_type": "pdf",
  "ingestion_timestamp": "ISO8601"
}

6. Storage Rules (IMPORTANT)
We store in Qdrant:

vector

payload

We do NOT store:

raw text

full chunks

documents

embeddings cache

Text lives in:

storage/chunks/<doc_id>_chunks.json

7. Insertion Strategy (MANDATORY)
Always use UPSERT
client.upsert(
    collection_name="rag_chunks",
    points=[...]
)


Why:

idempotent

safe

repeatable

production-safe

8. Batch Strategy

Batch size: 100–500 points

Never insert one by one

Never insert entire document in one request

9. Collection Auto-Creation

On startup:

if not client.collection_exists("rag_chunks"):
    client.create_collection(...)


This allows:

clean startup

no manual setup

CI/CD compatible

10. Validation Rules (HARD FAIL)

Reject insertion if:

embedding dim ≠ 3072

chunk_id missing

doc_id missing

vector is empty

payload not JSON-serializable

No silent failures allowed.

11. Directory Structure
storage/
 ├── chunks/
 │    └── <doc_id>_chunks.json
 ├── embeddings/
 │    └── <doc_id>.json
 └── qdrant/
      └── (docker volume)

12. Logging Requirements

Must log:

collection creation

batch upserts

total points inserted

doc_id

errors (full traceback)

13. What GLM MUST Implement
Rewrite vector_store.py to include:

Qdrant client

create collection if missing

upsert embeddings

validate dimensions

build payload from metadata

batch insertion

strong logging

zero retrieval logic

14. Integration Point

Inside /rag/upload endpoint:

upload
 └─> chunking
     └─> embedding
         └─> vector_store.upsert(doc_id)
             └─> return success

15. Why This Is Production-Grade

✅ Deterministic IDs
✅ Idempotent writes
✅ Persistent storage
✅ Metadata preserved
✅ Filter-ready
✅ Cloud-migratable
✅ Debuggable
✅ CI/CD friendly
✅ Scales to millions of vectors

16. What Is Explicitly Out of Scope

🚫 Retrieval
🚫 Reranking
🚫 Hybrid search
🚫 Query logic
🚫 Prompting
🚫 LLM calls

These will be handled later.