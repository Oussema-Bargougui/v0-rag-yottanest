# RAG System Integration Guide

## Overview

This guide provides complete instructions to integrate the RAG (Retrieval-Augmented Generation) system into `backend/rag_researcher` without breaking any existing functionality.

---

## Objectives

1. Integrate RAG system into `backend/rag_researcher`
2. Preserve all existing RAG functionality (no changes to core logic)
3. Preserve existing project structure (no breaking changes)
4. Add 2 new endpoints for testing via Swagger UI
5. Maintain all existing API endpoints from both systems
6. Keep clear, comprehensive logging for debugging
7. Ensure Swagger UI works with all endpoints

---

## Part 1: RAG System Architecture

### What is RAG?

RAG (Retrieval-Augmented Generation) combines:
- Retrieval: Finding relevant documents from a knowledge base
- Generation: Using an LLM to generate answers based on retrieved documents

### How This RAG System Works

```
┌─────────────┐
│  DOCUMENT   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Load Document (PDF, TXT, DOCX, HTML)                      │
│ 2. Extract Text (OCR if needed)                               │
│ 3. Chunk Text (Semantic Splitting - 150-700 chars)           │
│ 4. Extract Metadata (author, date, page, etc.)               │
│ 5. Embed Chunks (OpenRouter: text-embedding-3-small)         │
│ 6. Store in Qdrant Cloud (1536-dimensional vectors)          │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                       QDRANT CLOUD                           │
├─────────────────────────────────────────────────────────────┤
│ - Collections (separate document groups)                     │
│ - Vectors (1536 dimensions per chunk)                        │
│ - Metadata (document info, chunk info)                       │
│ - Distance: Cosine similarity for retrieval                  │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      QUERY PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│ 1. Receive Query (user question)                            │
│ 2. Embed Query (same model as chunks)                        │
│ 3. Retrieve Relevant Chunks (Top-K: 30)                      │
│ 4. Rerank Chunks (if enabled - Top-K: 5)                    │
│ 5. Build Context (concatenate retrieved chunks)             │
│ 6. Generate Answer (OpenRouter: gpt-4o-mini)               │
│ 7. Return Answer + Sources + Evaluation Metrics            │
└─────────────────────────────────────────────────────────────┘
```

### System Layers

#### 1. Ingestion Layer (`src/ingestion/`)
- Purpose: Process documents into searchable chunks
- Components:
  - `document_loader/` - Load PDF, TXT, DOCX, HTML files
  - `chunking/` - Split text into semantic chunks
  - `metadata/` - Extract and enrich document metadata
- Key Functions:
  - Extract text from documents
  - Split text into coherent chunks
  - Embed chunks into vectors
  - Store in vector database

#### 2. Embeddings Layer (`src/embeddings/`)
- Purpose: Convert text to vector representations
- Provider: OpenRouter (text-embedding-3-small)
- Dimension: 1536
- Providers Available:
  - OpenRouter (default)
  - OpenAI
  - Cohere
  - Sentence Transformers
  - HuggingFace

#### 3. Vector Store Layer (`src/vectorstore/`)
- Purpose: Store and retrieve vector embeddings
- Provider: Qdrant Cloud
- Features:
  - Create collections
  - Insert vectors with metadata
  - Search by similarity
  - Filter by metadata
- Providers Available:
  - Qdrant (default)
  - Pinecone
  - Weaviate
  - PGVector

#### 4. LLM Layer (`src/llm/`)
- Purpose: Generate answers from context
- Provider: OpenRouter (gpt-4o-mini)
- Providers Available:
  - OpenRouter (default)
  - OpenAI
  - Anthropic
  - Ollama (local)
  - vLLM (local)

#### 5. RAG Pipeline (`src/rag/`)
- Purpose: Orchestrate retrieval and generation
- Components:
  - `retrieval/` - Find relevant documents
  - `generation/` - Generate answers with citations
  - `query_understanding/` - Analyze and expand queries
- Process:
  1. Understand query intent
  2. Expand query with synonyms
  3. Retrieve relevant chunks
  4. Rerank by relevance
  5. Generate answer
  6. Add citations

#### 6. Reranker Layer (`src/reranker/`)
- Purpose: Reorder retrieved results by relevance
- Providers:
  - Simple (default - no reranking)
  - Cross-Encoder
  - BGE Reranker
  - Cohere Rerank

#### 7. Evaluation Layer (`src/evaluation/`)
- Purpose: Measure RAG quality
- Metrics:
  - Retrieval: Precision@K, Recall@K, MRR
  - Generation: Faithfulness, Context Coverage
  - Optional: RAGAS (comprehensive evaluation)

#### 8. Core Layer (`src/core/`)
- Purpose: Configuration and shared infrastructure
- Components:
  - `config.py` - All settings (models, API keys, chunking)
  - `providers.py` - Singleton providers (initialized once)
  - `constants.py` - System constants
  - `exceptions.py` - Custom exceptions
  - `secrets.py` - API key management

#### 9. API Layer (`src/api/`)
- Purpose: FastAPI endpoints for external access
- Components:
  - `routes/` - Endpoint implementations
  - `schemas/` - Request/response models
  - `dependencies.py` - Shared dependencies
  - `app.py` - FastAPI application setup

### FastAPI Architecture

FastAPI provides:
- Fast performance (async/await)
- Automatic API documentation (Swagger UI)
- Type validation (Pydantic)
- Modern Python (3.8+)

### Logging System

All operations logged with clear output:
```python
logger.info("=" * 80)
logger.info("STEP 1: Initializing...")
logger.info("✓ Step completed")
```

Output Example:
```
2026-01-29 00:30:00 - __main__ - INFO - ================================================================================
2026-01-29 00:30:00 - __main__ - INFO - INGESTION STARTED
2026-01-29 00:30:01 - __main__ - INFO - [PDFLoader] Found 152 pages
```

---

## Part 2: Implementation Plan

### Target Location
```
YOTTANEST_PROJECT/
└── backend/
    └── rag_researcher/  ← INTEGRATE RAG HERE
```

### Target Architecture (After Integration)

```
backend/rag_researcher/
├── src/                              # ← COPIED from rag_search/
│   ├── api/                          # ← ALL API ENDPOINTS
│   │   ├── app.py                    # FastAPI setup
│   │   ├── dependencies.py           # Shared dependencies
│   │   ├── schemas/                  # Request/response models
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   └── routes/
│   │       ├── query.py              # Existing: POST /query
│   │       ├── ingest.py             # Existing: POST /api/v1/ingest*
│   │       ├── collections.py        # Existing: POST /api/v1/collections/*
│   │       ├── health.py             # Existing: GET /health
│   │       └── simple.py             # NEW: 2 simplified endpoints
│   │
│   ├── core/                         # Configuration
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── providers.py
│   │   └── secrets.py
│   │
│   ├── embeddings/                   # Embedding layer
│   ├── vectorstore/                  # Vector store layer
│   ├── ingestion/                    # Ingestion layer
│   ├── llm/                         # LLM layer
│   ├── rag/                         # RAG pipeline
│   ├── reranker/                    # Reranker layer
│   └── evaluation/                   # Evaluation layer
│
├── main.py                           # ← NEW: Service entry point
├── requirements.txt                  # ← ADD RAG dependencies
├── .env                             # ← NEW: RAG configuration
├── README.md                        # ← NEW: Documentation
│
├── pycache/                         # ← Existing (keep)
└── output/                          # ← Existing (keep)
```

---

## Part 3: Step-by-Step Implementation

### ⚠️ CRITICAL WARNINGS

1. DO NOT modify any RAG system code
   - Keep all functionality exactly as-is
   - Do not change imports (we use `src/` folder)
   - Do not modify core logic

2. DO NOT break existing project structure
   - Keep `pycache/` and `output/` folders
   - Do not modify other backend services

3. DO NOT delete without backup
   - Remove old files cleanly
   - No `_backup` folders

4. MUST verify everything works
   - Test all endpoints
   - Check Swagger UI
   - Verify logging output
   - Confirm Qdrant connectivity

---

### Step 1: Navigate to Target Directory

```bash
cd YOTTANEST_PROJECT/backend/rag_researcher
```

Verify location:
```bash
pwd
# Should output: .../YOTTANEST_PROJECT/backend/rag_researcher
```

---

### Step 2: Delete Old Files

Remove these files:
```bash
rm config.py
rm main.py
rm orchestrator.py
rm -rf modules/
```

Verify deletion:
```bash
ls -la
# Should NOT see: config.py, main.py, orchestrator.py, modules/
```

---

### Step 3: Copy RAG System (src/ Folder)

Copy entire `src` folder from RAG system:

```bash
cp -r ../../rag_search/src src/
```

Verify copy:
```bash
ls -la src/
# Should SEE: api/, core/, embeddings/, vectorstore/, ingestion/, llm/, rag/, reranker/, evaluation/
```

NO IMPORT CHANGES NEEDED. All imports use `from src.xxx` format.

---

### Step 4: Create 2 New Simplified Endpoints

Create file: `src/api/routes/simple.py`

```python
from fastapi import APIRouter, UploadFile, Form, HTTPException
from pydantic import BaseModel
from src.rag.pipeline import RAGPipeline
from src.ingestion.service import IngestionService
from src.vectorstore.base import VectorStoreProvider
from src.core.providers import get_vector_store, get_embedding_provider, get_llm_provider, get_reranker
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/simple", tags=["Simple Endpoints"])

class QueryRequest(BaseModel):
    collection_id: str
    query: str
    top_k: int = 5

@router.post("/ingest")
async def simple_ingest(
    collection_id: str = Form(...),
    file: UploadFile = Form(...),
    description: str = Form(default="")
):
    """
    Simplified Ingestion Endpoint
    
    Combines all ingestion steps in one call:
    1. Create collection (if doesn't exist)
    2. Upload document
    3. Extract text
    4. Chunk text
    5. Embed chunks
    6. Store in Qdrant Cloud
    
    Test via Swagger UI: http://localhost:8001/docs
    """
    try:
        logger.info("=" * 80)
        logger.info("SIMPLE INGESTION STARTED")
        logger.info(f"Collection ID: {collection_id}")
        logger.info(f"File: {file.filename}")
        logger.info("=" * 80)
        
        # Get vector store
        logger.info("Step 1: Initializing vector store...")
        vector_store: VectorStoreProvider = get_vector_store()
        
        # Create collection (if doesn't exist)
        logger.info("Step 2: Creating collection...")
        try:
            vector_store.create_collection(
                collection_name=collection_id,
                dimension=settings.embedding_dimension,
                description=description
            )
            logger.info(f"✓ Collection '{collection_id}' created")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"✓ Collection '{collection_id}' already exists")
            else:
                raise
        
        # Ingest document
        logger.info("Step 3: Ingesting document...")
        ingestion_service = IngestionService(
            vector_store=vector_store,
            embedding_provider=get_embedding_provider()
        )
        
        content = await file.read()
        result = await ingestion_service.ingest_document(
            collection_name=collection_id,
            file_content=content,
            filename=file.filename,
            file_type=file.content_type
        )
        
        logger.info("=" * 80)
        logger.info("✓ SIMPLE INGESTION COMPLETED")
        logger.info(f"Chunks stored: {result['chunks_stored']}")
        logger.info("=" * 80)
        
        return {
            "collection_id": collection_id,
            "status": "completed",
            "chunks_stored": result["chunks_stored"],
            "message": f"Document '{file.filename}' successfully ingested"
        }
        
    except Exception as e:
        logger.error(f"❌ SIMPLE INGESTION FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def simple_query(request: QueryRequest):
    """
    Simplified Query Endpoint
    
    Query documents in collection using RAG.
    Returns:
    - Answer (AI-generated)
    - Sources (document references)
    - Chunks used
    - Query time
    - Evaluation metrics (optional)
    
    Test via Swagger UI: http://localhost:8001/docs
    """
    try:
        logger.info("=" * 80)
        logger.info("SIMPLE QUERY STARTED")
        logger.info(f"Collection ID: {request.collection_id}")
        logger.info(f"Query: {request.query}")
        logger.info(f"Top K: {request.top_k}")
        logger.info("=" * 80)
        
        # Initialize RAG pipeline
        logger.info("Step 1: Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline(
            vector_store=get_vector_store(),
            embedding_provider=get_embedding_provider(),
            llm_provider=get_llm_provider(),
            reranker_provider=get_reranker()
        )
        
        # Run query
        logger.info("Step 2: Running query...")
        result = await rag_pipeline.query(
            collection_name=request.collection_id,
            query=request.query,
            top_k=request.top_k
        )
        
        logger.info("=" * 80)
        logger.info("✓ SIMPLE QUERY COMPLETED")
        logger.info(f"Answer generated: {len(result['answer'])} chars")
        logger.info(f"Sources: {result['sources']}")
        logger.info("=" * 80)
        
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "chunks_used": result.get("chunks_used", 0),
            "query_time_ms": result.get("query_time_ms", 0),
            "evaluation": result.get("evaluation", {})
        }
        
    except Exception as e:
        logger.error(f"❌ SIMPLE QUERY FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

Verify file creation:
```bash
ls -la src/api/routes/
# Should SEE: simple.py
```

---

### Step 5: Update API App

Create file: `src/api/app.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Researcher Service",
    version="0.1.0",
    description="Production-Grade RAG Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing routes
from src.api.routes import query, ingest, collections, health
app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(collections.router)
app.include_router(health.router)

# Include new simplified routes
from src.api.routes import simple
app.include_router(simple.router)

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("STARTING RAG RESEARCHER SERVICE")
    logger.info("=" * 80)
    from src.core.providers import initialize_shared_providers
    initialize_shared_providers()
    logger.info("✓ All shared providers initialized")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("SHUTTING DOWN RAG RESEARCHER SERVICE")
    logger.info("=" * 80)
```

Verify file creation:
```bash
cat src/api/app.py
```

---

### Step 6: Create Main Entry Point

Create file: `main.py`

```python
import uvicorn
from src.api.app import app

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
```

Verify file creation:
```bash
cat main.py
```

---

### Step 7: Create .env Configuration

Create file: `.env`

```bash
# =====================================================
# OPENROUTER CONFIGURATION
# =====================================================
OPENROUTER_API_KEY=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
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# =====================================================
# LLM CONFIGURATION
# =====================================================
LLM_MODEL=openai/gpt-4o-mini
LLM_PROVIDER=openrouter

# =====================================================
# EMBEDDING CONFIGURATION
# =====================================================
EMBEDDING_MODEL=openai/text-embedding-3-small
EMBEDDING_PROVIDER=openrouter
EMBEDDING_DIMENSION=1536

# =====================================================
# CHUNKING CONFIGURATION
# =====================================================
CHUNKING_STRATEGY=semantic
SEMANTIC_SIMILARITY_THRESHOLD=0.65
MAX_CHUNK_SIZE=700
MIN_CHUNK_SIZE=150
CHUNK_OVERLAP=80
ENABLE_PDF_OCR=false

# =====================================================
# RETRIEVAL & RERANKING
# =====================================================
ENABLE_RERANKING=true
RERANKER_PROVIDER=simple
RETRIEVAL_TOP_K=30
FINAL_TOP_K=5
RERANKING_MIN_SCORE=0.45

# =====================================================
# EVALUATION
# =====================================================
ENABLE_EVALUATION=true
EVALUATION_DEFAULT_K=5
EVALUATION_LOG_RESULTS=true
EVALUATION_STORE_HISTORY=false
ENABLE_RAGAS=false

# =====================================================
# QDRANT CLOUD CONFIGURATION
# =====================================================
QDRANT_URL=https://52e7417e-4d71-47c4-ba76-caaa39d0a276.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.rd1phzFfrcqN3Oy2fN8Q3tV50M1GusSdCtpqO-jqbeU

# =====================================================
# DEMO/DEVELOPMENT
# =====================================================
SEED_DEMO_DOCUMENTS=false
```

Verify file creation:
```bash
cat .env
```

---

### Step 8: Update requirements.txt

Append these dependencies to existing `requirements.txt`:

```bash
# RAG Researcher Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pypdf==3.17.4
qdrant-client==1.7.3
```

Method: Open requirements.txt in text editor and append above lines to end.

Verify append:
```bash
cat requirements.txt
```

---

### Step 9: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 10: Create README Documentation

Create file: `README.md`

```markdown
# RAG Researcher Service

## Overview

Production-grade Retrieval-Augmented Generation (RAG) system.

## Architecture

```
src/
├── api/           - All API endpoints (FastAPI)
├── core/          - Configuration
├── embeddings/     - Text to vectors
├── vectorstore/    - Vector database (Qdrant)
├── ingestion/      - Document processing
├── llm/           - Answer generation
├── rag/           - RAG orchestration
├── reranker/      - Result reranking
└── evaluation/    - Quality metrics
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

See `.env` file for all settings.

## Running

```bash
python main.py
```

Service starts at: `http://localhost:8001`

## API Documentation

### Swagger UI
Open: `http://localhost:8001/docs`

### Available Endpoints

#### Existing Endpoints

**Query:**
- `POST /query` - Query RAG system

**Ingestion:**
- `POST /api/v1/ingest` - Ingest document
- `POST /api/v1/ingest/text` - Ingest text
- `GET /api/v1/ingest/formats` - Get supported formats

**Collections:**
- `POST /api/v1/collections/create` - Create collection
- `POST /api/v1/collections/{id}/ingest` - Ingest into collection
- `POST /api/v1/collections/{id}/query` - Query collection
- `DELETE /api/v1/collections/{id}` - Delete collection

**Health:**
- `GET /` - Root endpoint
- `GET /health` - Health check

#### New Simplified Endpoints

- `POST /api/v1/simple/ingest` - Upload + process (one call)
- `POST /api/v1/simple/query` - Query documents

## Testing

Test all endpoints via Swagger UI at `http://localhost:8001/docs`

## Logging

All operations logged with clear output.

## Troubleshooting

See `COMPREHENSIVE_RAG_DOCUMENTATION.md` for details.
```

Verify file creation:
```bash
cat README.md
```

---

### Step 11: Verify Structure

Check final structure:
```bash
tree -L 2 -I '__pycache__|*.pyc'
```

Expected output:
```
.
├── main.py
├── README.md
├── requirements.txt
├── .env
├── pycache/
├── output/
└── src/
    ├── api/
    ├── core/
    ├── embeddings/
    ├── vectorstore/
    ├── ingestion/
    ├── llm/
    ├── rag/
    ├── reranker/
    └── evaluation/
```

---

## Part 4: Testing & Verification

### Test 1: Start Service

```bash
python main.py
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
2026-01-29 00:35:00 - src.api.app - INFO - ================================================================================
2026-01-29 00:35:00 - src.api.app - INFO - STARTING RAG RESEARCHER SERVICE
2026-01-29 00:35:00 - src.api.app - INFO - ================================================================================
2026-01-29 00:35:01 - src.core.providers - INFO - [EmbeddingFactory] Creating OpenRouter embedding provider
2026-01-29 00:35:01 - src.embeddings.providers.openrouter - INFO - [OpenRouterEmbeddingProvider] Initialized with model: openai/text-embedding-3-small
2026-01-29 00:35:01 - src.embeddings.providers.openrouter - INFO - [OpenRouterEmbeddingProvider] Expected dimension: 1536
2026-01-29 00:35:01 - src.core.providers - INFO - [Providers] Shared embedding provider initialized
2026-01-29 00:35:01 - src.vectorstore.providers.qdrant - INFO - [QdrantProvider] Connecting to Qdrant Cloud...
2026-01-29 00:35:02 - src.core.providers - INFO - [Providers] Shared vector store initialized
2026-01-29 00:35:02 - src.core.providers - INFO - [Providers] Vector store mode: cloud
2026-01-29 00:35:02 - src.api.app - INFO - ✓ All shared providers initialized
2026-01-29 00:35:02 - src.api.app - INFO - ================================================================================
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

SUCCESS: Service starts without errors.

---

### Test 2: Access Swagger UI

Open browser: `http://localhost:8001/docs`

Expected:
- Swagger UI loads
- All endpoints visible
- "Simple Endpoints" section with 2 new endpoints

---

### Test 3: Test Simple Ingestion via Swagger UI

1. Open Swagger UI: `http://localhost:8001/docs`
2. Find "Simple Endpoints" section
3. Click "POST /api/v1/simple/ingest"
4. Click "Try it out"
5. Fill in form:
   - collection_id: `test_collection`
   - file: Select a PDF file
   - description: (optional)
6. Click "Execute"

Expected logs:
```
2026-01-29 00:40:00 - src.api.routes.simple - INFO - ================================================================================
2026-01-29 00:40:00 - src.api.routes.simple - INFO - SIMPLE INGESTION STARTED
2026-01-29 00:40:00 - src.api.routes.simple - INFO - Collection ID: test_collection
2026-01-29 00:40:00 - src.api.routes.simple - INFO - File: test.pdf
2026-01-29 00:40:00 - src.api.routes.simple - INFO - ================================================================================
2026-01-29 00:40:00 - src.api.routes.simple - INFO - Step 1: Initializing vector store...
2026-01-29 00:40:00 - src.api.routes.simple - INFO - Step 2: Creating collection...
2026-01-29 00:40:01 - src.api.routes.simple - INFO - ✓ Collection 'test_collection' created
2026-01-29 00:40:01 - src.api.routes.simple - INFO - Step 3: Ingesting document...
...
2026-01-29 00:40:05 - src.api.routes.simple - INFO - ✓ SIMPLE INGESTION COMPLETED
2026-01-29 00:40:05 - src.api.routes.simple - INFO - Chunks stored: 45
```

Expected response:
```json
{
  "collection_id": "test_collection",
  "status": "completed",
  "chunks_stored": 45,
  "message": "Document 'test.pdf' successfully ingested"
}
```

---

### Test 4: Test Simple Query via Swagger UI

1. In Swagger UI
2. Find "Simple Endpoints" section
3. Click "POST /api/v1/simple/query"
4. Click "Try it out"
5. Fill in JSON body:
```json
{
  "collection_id": "test_collection",
  "query": "What is this document about?",
  "top_k": 5
}
```
6. Click "Execute"

Expected logs:
```
2026-01-29 00:45:00 - src.api.routes.simple - INFO - ================================================================================
2026-01-29 00:45:00 - src.api.routes.simple - INFO - SIMPLE QUERY STARTED
2026-01-29 00:45:00 - src.api.routes.simple - INFO - Collection ID: test_collection
2026-01-29 00:45:00 - src.api.routes.simple - INFO - Query: What is this document about?
2026-01-29 00:45:00 - src.api.routes.simple - INFO - Top K: 5
2026-01-29 00:45:00 - src.api.routes.simple - INFO - ================================================================================
...
2026-01-29 00:45:03 - src.api.routes.simple - INFO - ✓ SIMPLE QUERY COMPLETED
2026-01-29 00:45:03 - src.api.routes.simple - INFO - Answer generated: 234 chars
2026-01-29 00:45:03 - src.api.routes.simple - INFO - Sources: ["test.pdf"]
```

Expected response:
```json
{
  "answer": "Based on the document...",
  "sources": ["test.pdf"],
  "chunks_used": 5,
  "query_time_ms": 1250,
  "evaluation": {}
}
```

---

## Part 5: Troubleshooting Guide

### Issue 1: Service Won't Start

Symptoms: ImportError, ModuleNotFoundError, port in use

Solutions:
```bash
# Check Python version
python --version

# Check dependencies
pip list | grep -E "fastapi|uvicorn|qdrant"

# Check port
netstat -ano | findstr :8001
```

---

### Issue 2: ImportError (src not found)

Symptoms: ModuleNotFoundError: No module named 'src'

Solutions:
```bash
# Verify structure
ls -la src/

# Check directory
pwd
# Should be: .../YOTTANEST_PROJECT/backend/rag_researcher
```

---

### Issue 3: OpenRouter API Error (401)

Symptoms: 401 Unauthorized, User not found

Solutions:
1. Check API key in .env
```bash
grep OPENROUTER_API_KEY .env
```

2. Verify OpenRouter credits at: https://openrouter.ai/credits

3. Test API key manually:
```bash
curl -X POST https://openrouter.ai/api/v1/embeddings \
  -H "Authorization: Bearer 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" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/text-embedding-3-small","input":"test"}'
```

4. Check OpenRouter status at: https://openrouter.ai

---

### Issue 4: Qdrant Connection Error

Symptoms: ConnectionError: Cannot connect to Qdrant

Solutions:
1. Check Qdrant URL in .env
```bash
grep QDRANT_URL .env
```

2. Test Qdrant Cloud at: https://cloud.qdrant.io

3. Test connection:
```bash
curl https://52e7417e-4d71-47c4-ba76-caaa39d0a276.europe-west3-0.gcp.cloud.qdrant.io
```

---

### Issue 5: PDF Processing Error

Symptoms: PDF extraction failed, pypdf error

Solutions:
1. Enable OCR for scanned PDFs in .env:
```
ENABLE_PDF_OCR=true
```

2. Install OCR dependencies:
```bash
pip install pytesseract
```

3. Check PDF file type:
```bash
file test.pdf
```

---

### Issue 6: Swagger UI Not Loading

Symptoms: Page not found, 404 error

Solutions:
1. Check service is running:
```bash
curl http://localhost:8001/
```

2. Check logs for errors

3. Clear browser cache (Ctrl+Shift+Delete)

4. Try alternative URL: `http://localhost:8001/redoc`

---

## Part 6: Final Verification Checklist

### Pre-Deployment Checklist

- [ ] Service starts without errors
- [ ] Swagger UI loads at `http://localhost:8001/docs`
- [ ] All endpoints visible in Swagger UI
- [ ] New endpoints work: `/api/v1/simple/ingest`
- [ ] New endpoints work: `/api/v1/simple/query`
- [ ] Existing RAG endpoints still work
- [ ] Logging output is clear and comprehensive
- [ ] Qdrant Cloud connection successful
- [ ] OpenRouter API working (embeddings + LLM)
- [ ] Document ingestion works (PDF, TXT, etc.)
- [ ] Query works and returns answers
- [ ] No import errors
- [ ] No port conflicts

### Performance Checklist

- [ ] Ingestion completes in reasonable time
- [ ] Query completes in reasonable time
- [ ] Memory usage is stable
- [ ] No memory leaks

---

## Part 7: Summary

### What Was Done

1. Deleted old files
2. Copied RAG system
3. Added 2 new endpoints
4. Created .env
5. Updated requirements.txt
6. Created documentation
7. Verified structure

### What Was NOT Changed

1. No RAG code modified
2. No import changes
3. No other services affected
4. No breaking changes

### Key Points

- Service runs on port 8001
- Swagger UI at `http://localhost:8001/docs`
- Qdrant Cloud configured
- OpenRouter API keys configured
- All logging is clear
- No code changes needed to RAG system

### Next Steps

1. Test thoroughly
2. Verify Swagger UI works
3. Monitor performance
4. Document any issues

---

## Conclusion

This guide provides complete step-by-step instructions to integrate RAG system without breaking any functionality.

### Key Success Factors

1. Follow steps exactly in order
2. Copy .env file exactly as shown
3. Do not modify RAG code
4. Test each step before proceeding
5. Verify logging output
6. Check Swagger UI works

### Result

- Clean, working RAG integration
- All existing functionality preserved
- New endpoints available
- Comprehensive logging
- Team-ready documentation

For additional details, see `COMPREHENSIVE_RAG_DOCUMENTATION.md`