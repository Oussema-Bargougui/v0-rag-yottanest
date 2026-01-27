# Yottanest RAG System – Production Redesign Contract

⚠️ THIS FILE IS A STRICT CONTRACT  
READ IT COMPLETELY BEFORE WRITING ANY CODE.

You are ONLY allowed to work on:
backend/rag_researcher/

You must NOT touch:
- frontend
- web-researcher
- VAT system
- company search
- any other backend modules
- backend main server logic (main.py remains the server entry)

---

# OBJECTIVE

Upgrade ONLY the RAG system into a **production-grade, multimodal, bank-level RAG pipeline** for AML/KYC document analysis.

This is NOT a demo system.
This is NOT an academic system.
This is a system designed for banks.

---

# IMPORTANT TECHNOLOGY DECISION

❌ DO NOT use Ollama  
❌ DO NOT use local LLaMA  
❌ DO NOT use any local LLM

✅ Use OpenRouter API for ALL LLM calls  
(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, this is the api key for open router add it in the .env plus we will be using chatgpt 4o mini)

---

# SCOPE OF WORK (STRICT)

You are allowed to:
- replace DataLoader implementation
- add RAG FastAPI endpoints
- add health check
- add image + table extraction
- add image captioning using OpenRouter
- return structured JSON

You are NOT allowed to:
- touch frontend
- change backend main.py server behavior
- modify non-RAG services
- implement embeddings yet
- implement chunking yet
- implement retrieval yet

---

# CURRENT ARCHITECTURE RULE

`main.py` is already the backend server.  
DO NOT replace it.  
DO NOT create another server.

You will:
- register RAG router
- add endpoints under /rag/*
- add /health endpoint
- keep everything else unchanged

---

# PHASE 1 — FASTAPI RAG ENDPOINTS

You must expose these endpoints:

## 1. Health Check
GET /health

css
Copier le code

Response:
```json
{ "status": "ok" }
2. Upload Document
bash
Copier le code
POST /rag/upload
Accepts file upload (PDF, DOCX, TXT, MD)

Uses new DataLoader

Extracts text, tables, images

Generates image captions using OpenRouter

Injects captions into document structure

Returns structured JSON

NO embedding

NO chunking

NO retrieval

PHASE 2 — DATALOADER REPLACEMENT (MANDATORY)
You must REPLACE the existing DataLoader.

The old DataLoader is PROTOTYPE LEVEL.
It flattens text and loses structure.
It must be fully replaced.

New DataLoader responsibilities
DataLoader must:

Accept uploaded files

Support PDF, DOCX, TXT, MD

Extract pages

Preserve layout

Extract text blocks

Extract tables with rows/columns

Extract images with page & bbox

Save images to storage

Generate image captions

Inject captions back into structure

Return structured JSON

Output format (STRICT)
json
Copier le code
{
  "doc_id": "uuid",
  "filename": "file.pdf",
  "pages": [
    {
      "page_number": 1,
      "text_blocks": [...],
      "tables": [
        {
          "table_id": "...",
          "headers": [...],
          "rows": [...],
          "semantic_text": "..."
        }
      ],
      "images": [
        {
          "image_id": "...",
          "path": "...",
          "caption": "...",
          "business_summary": "...",
          "page": 1,
          "bbox": [...]
        }
      ]
    }
  ],
  "metadata": {
    "source": "upload",
    "file_type": "pdf",
    "created_at": "ISO8601"
  }
}
PHASE 3 — IMAGE HANDLING (CRITICAL)
For every image:

Extract raw image

Save it (local storage is OK for now)

Call OpenRouter Vision model to generate:

factual caption (mandatory)

business summary (optional)

Inject both texts into the document structure

Store metadata (page, bbox, id)

⚠️ Raw images are NEVER embedded
⚠️ Only captions & summaries will be embedded later

PHASE 4 — TABLE HANDLING (CRITICAL)
For tables:

Extract structure

Preserve headers & rows

Generate semantic text description

Store table metadata

Link to page number

Keep original structure

PHASE 5 — CONFIGURATION (MANDATORY)
Create:

.env

config.py

.env must include:

ini
Copier le code
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=...
VISION_MODEL=...
STORAGE_PATH=...
DO NOT hardcode keys in code.

PHASE 6 — PROJECT RULES (STRICT)
Do NOT touch frontend

Do NOT touch non-RAG backend

Do NOT add embeddings

Do NOT add chunking

Do NOT add retrieval

Do NOT refactor unrelated code

Only work inside rag_researcher

main.py remains the backend server

SUCCESS CRITERIA

When running:

uvicorn main:app --reload


Swagger (/docs) must show:

GET /health

POST /rag/upload

Uploading a document must return structured JSON
with text, tables, images, captions, metadata.

NEXT PHASE (DO NOT IMPLEMENT YET)

After validation:

chunking

embedding

vector DB

retrieval

reranking

evaluation