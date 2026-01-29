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