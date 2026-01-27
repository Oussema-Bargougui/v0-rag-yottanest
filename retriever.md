1. Purpose of the Retriever

The retriever is responsible for selecting the most relevant document chunks from the vector store and delivering a clean, minimal, high-signal context to the LLM.

This retriever is designed to be:

✅ Accurate (high semantic recall + precision)

✅ Fast (low latency)

✅ Cheap (minimal model calls)

✅ Deterministic (easy to debug)

✅ Scalable (works from 1k → 100M chunks)

✅ Model-agnostic (can swap models easily)

2. High-Level Retrieval Architecture

We use a two-stage retrieval pipeline:

User Query
   ↓
Query Embedding
   ↓
Dense Vector Search (Qdrant)
   ↓
Top-K Candidates (high recall)
   ↓
Cross-Encoder Reranker (high precision)
   ↓
Final Top-N Context Chunks
   ↓
LLM

3. Why This Architecture (Industry Standard)

This architecture is used by:

OpenAI RAG

Perplexity

Cohere Search

Azure AI Search

LangChain production templates

LlamaIndex production templates

Reason:

Dense retrievers give recall, rerankers give precision.

No single retriever can do both efficiently.

4. Stage 1: Dense Retrieval (Qdrant)
4.1 Retriever Type

Dense vector retriever using cosine similarity.

Database: Qdrant

Distance: Cosine

Embedding model: text-embedding-3-large (3072-dim)

Storage: Chunk-level

Metadata-aware

4.2 Query Flow

User query is embedded using the same embedding model

Query vector is sent to Qdrant

Qdrant returns top-K candidate chunks

Metadata is preserved (no loss)

4.3 Search Parameters
Parameter	Value	Reason
top_k	30–50	High recall before rerank
distance	cosine	Best for semantic embeddings
with_payload	true	Needed for reranking + context
with_vector	false	Reduce payload size
filter	optional	Doc-level filtering
4.4 Metadata Used

Each retrieved chunk contains:

{
  "doc_id": "...",
  "chunk_id": "...",
  "chunk_index": 12,
  "section_hint": "Financial Summary",
  "char_start": 10293,
  "char_end": 11012,
  "chunk_size": 512,
  "source": "pdf",
  "page": 7
}


This metadata is critical for:

reranking

deduplication

ordering

debugging

citation

traceability

5. Stage 2: Cross-Encoder Reranking (CRITICAL)
5.1 Why Reranking is Mandatory

Dense retrieval returns semantically related, not necessarily answer-relevant chunks.

Cross-encoder rerankers:

read the full query + chunk together

score relevance precisely

eliminate noise

reorder by actual usefulness

This step gives +30–50% precision in real systems.

6. Reranker Model Choice (Professional)
🏆 Recommended Model
BAAI/bge-reranker-large

Why this model:

State-of-the-art open-source reranker

Beats Cohere Rerank v3 in many benchmarks

Free

Local or API

Extremely stable

Designed for RAG

Specs:

Input: (query, chunk)

Output: relevance score

Type: Cross-encoder

Latency: ~10–20ms per pair (GPU) / ~50–80ms (CPU)

Context length: 512–1024 tokens

Alternative (if needed later)
Model	When to use
Cohere rerank v3.5	API only, fast setup
jina-reranker-v2	Lightweight
bge-reranker-base	Lower cost
gpt-4o-mini rerank prompt	Only for research
7. Reranking Flow
Input: 40 chunks from Qdrant
↓
Create (query, chunk_text) pairs
↓
Cross-encoder scores each pair
↓
Sort by score
↓
Keep top 5–8 chunks

8. Final Context Assembly

After reranking:

Deduplicate by chunk_id

Preserve original order if same section

Merge adjacent chunks (optional)

Trim context to token budget

Add section hints

Final context is clean, minimal, and accurate.

9. Retriever Configuration (Recommended Defaults)
dense_retriever:
  top_k: 40
  distance: cosine
  filters: optional

reranker:
  model: BAAI/bge-reranker-large
  top_n: 6
  batch_size: 16
  normalize_scores: true

context:
  max_chunks: 6
  max_tokens: 3500

10. What We Are NOT Using (By Design)
Method	Reason
BM25	Weak semantic recall
MultiQuery	Expensive + unstable
Ensemble	Complex, slow
Parent retriever	Metadata already solves this
LLM-based ranking	Too slow, too costly
11. Logging & Observability (MANDATORY)

We log:

retrieved chunk IDs

rerank scores

dropped chunks

final selected chunks

latency per stage

token counts

This allows:

debugging

retriever tuning

failure analysis

eval (RAGAS)

12. Evaluation Strategy

We evaluate retrieval using:

context_recall

context_precision

entity_recall

faithfulness

answer_relevance

(RAGAS-based)

13. Summary (Decision Locked)
✅ Final Retriever Choice
Stage	Model
Retrieval	Dense Qdrant
Ranking	BGE Cross-Encoder
Assembly	Metadata-aware

This is production-grade, scalable, clean, and proven.