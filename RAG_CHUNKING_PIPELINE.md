# RAG Chunking Pipeline (Production Level)

## Status
This file defines the **official chunking architecture** for the Yottanest RAG system.
This is a **bank-grade, production-ready** design and must be followed strictly.

The goal is to:
- Preserve semantic coherence
- Avoid page-boundary errors
- Preserve full metadata traceability
- Enable high-accuracy retrieval
- Support reranking, evaluation, and citations
- Scale to large multi-document ingestion

This pipeline comes **AFTER extraction and cleaning** and **BEFORE embedding**.

---

## ❗ Important Principles (DO NOT VIOLATE)

1. **Never chunk per page**
   Pages are layout artifacts, not semantic units.

2. **Always chunk on a full document stream**
   Pages must be merged into a continuous text stream.

3. **Always preserve metadata**
   Page numbers, document name, and source ranges MUST be attached to chunks.

4. **Chunks are retrieval units, pages are traceability units**
   They are different things.

5. **Chunking must be deterministic and reproducible**
   Same input → same chunks.

---

# 🏗️ Pipeline Overview

Extraction (pages)
↓
Cleaning (pages)
↓
Merge pages into document stream
↓
Chunking (2 strategies)
↓
Attach metadata
↓
Store chunks for retrieval

yaml
Copier le code

---

# 1️⃣ Input Format (from Text Cleaner)

Each document arrives as:

```json
{
  "doc_id": "uuid",
  "document_name": "file.pdf",
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "metadata": {...}
    }
  ]
}
This structure MUST NOT be modified.

2️⃣ Build the Document Stream (MANDATORY)
Before chunking, all pages must be merged into a single text stream.

Required logic:
python
Copier le code
full_text = ""
page_map = []

for page in pages:
    start = len(full_text)
    full_text += page["text"] + "\n\n"
    end = len(full_text)

    page_map.append({
        "page_number": page["page_number"],
        "start_char": start,
        "end_char": end
    })
Why:
This allows chunking across page boundaries while preserving traceability.

3️⃣ Chunking Strategy 1: Semantic Percentile Chunking
File:
bash
Copier le code
modules/chunking/semantic_percentile_chunker.py
Goal:
Create chunks based on semantic density, not fixed size.

Algorithm:
Split full_text into sentences

Embed each sentence

Compute semantic similarity between adjacent sentences

Compute similarity deltas

Find percentile threshold (e.g. 25%)

Create chunk boundaries where similarity drops

Enforce:

min_tokens

max_tokens

Merge small chunks if needed

Output chunk schema:
json
Copier le code
{
  "chunk_id": "uuid",
  "doc_id": "doc_123",
  "text": "...",
  "strategy": "semantic_percentile",
  "page_numbers": [10, 11],
  "char_range": [8421, 10122],
  "position": 12
}
4️⃣ Chunking Strategy 2: Similarity Matrix Clustering
File:
bash
Copier le code
modules/chunking/similarity_cluster_chunker.py
Goal:
Group sentences into semantic clusters using similarity thresholding.

Algorithm:
Split full_text into sentences

Embed all sentences

Build similarity matrix

Use threshold (e.g. 0.75)

Build clusters by adjacency

Merge sentences per cluster

Enforce:

max_tokens

min_tokens

Preserve order of clusters

Output chunk schema:
json
Copier le code
{
  "chunk_id": "uuid",
  "doc_id": "doc_123",
  "text": "...",
  "strategy": "similarity_cluster",
  "page_numbers": [5, 6, 7],
  "char_range": [4500, 7890],
  "position": 8
}
5️⃣ Metadata Reattachment (MANDATORY)
After chunk creation, page metadata MUST be reattached.

Logic:
python
Copier le code
chunk_pages = [
    p["page_number"]
    for p in page_map
    if p["start_char"] <= chunk_end
    and p["end_char"] >= chunk_start
]
This allows:

citations

auditability

reranking explanations

evaluation

6️⃣ Chunk Storage Format
Chunks must be stored in:

pgsql
Copier le code
storage/chunks/
  ├── doc_id/
       ├── semantic_chunks.json
       ├── cluster_chunks.json
Each file contains a list of chunks.

7️⃣ Why We Use Two Chunkers
Chunker	Strength
Semantic Percentile	Narrative flow
Similarity Clustering	Topic grouping

Later, retrieval will:

combine both

rerank

compress

evaluate

8️⃣ DO NOT DO THESE
❌ Chunk per page
❌ Chunk before cleaning
❌ Lose page metadata
❌ Chunk raw PDF text
❌ Merge pages without char map
❌ Use fixed token split only

9️⃣ Success Criteria
Chunks can cross page boundaries

Metadata preserved

Chunks explainable

Deterministic output

Supports multi-document ingestion

Ready for hybrid retrieval

10️⃣ Next Stage (NOT NOW)
After chunking:

embedding

hybrid retriever

reranking

compression

evaluation

✅ This file is the single source of truth for chunking.
you must follow it strictly.
If something is unclear, you MUST ask before implementing.