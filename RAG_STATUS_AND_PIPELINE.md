RAG Ingestion Pipeline – Current Status, Decisions & Next Steps (Bank-Grade Project)

1. Project Context

This project is a production-grade multimodal RAG system designed for banking / AML / KYC / compliance use cases.

This is NOT:

a demo RAG

a research experiment

a toy project

a chatbot

This system must be:

deterministic

auditable

explainable

accurate on multiple long documents

production-ready

bank-safe

2. Scope of Work (Current Phase)

We are currently building the ingestion pipeline, which consists of:

UPLOAD → EXTRACTION → CLEANING → (NEXT: CHUNKING)


Only ingestion is in scope right now.
No retrieval, no generation yet.

3. What Is Already Implemented (DO NOT REWRITE)
✅ 3.1 Upload Endpoint

Endpoint:

POST /rag/upload


Capabilities:

accepts single or multiple files

supports PDF / DOCX / TXT / MD

generates doc_id per document

processes each document independently

does not crash batch if one fails

returns extraction response (unchanged)

✅ 3.2 Extraction Layer (data_loader.py)

Already working and stable.

Extraction outputs:

page-based structure

raw text per page

table text per page

image placeholders per page

metadata per page

images saved to storage/images

extraction saved to storage/extraction/<doc_id>.json

DO NOT touch extraction logic.

✅ 3.3 Extraction Persistence

Storage:

storage/
 ├── extraction/
 │    └── <doc_id>.json
 ├── images/
 │    └── <doc_id>_page_X_img_Y.png


This is mandatory for audit and debugging.

✅ 3.4 Image Handling (Partial)

images are detected and saved

placeholders injected into text

metadata contains image_ids

caption extraction exists

description generation using LLM is still being fixed

This is acceptable for now. Not blocking.

4. New Component: RAGTextCleaner (JUST ADDED)
Purpose

Normalize text WITHOUT losing data before chunking.

File
modules/rag_text_cleaner.py

Key principles:

lossless cleaning

page-by-page

metadata preserved

no LLM

no refactor of extraction

no schema changes

Input:
storage/extraction/<doc_id>.json

Output:
storage/cleaned/<doc_id>.json

5. Current Pipeline (FINAL DESIGN – DO NOT CHANGE)
POST /rag/upload
   ↓
data_loader.py  → extraction JSON
   ↓
save extraction/<doc_id>.json
   ↓
RAGTextCleaner.clean_extracted_document()
   ↓
save cleaned/<doc_id>.json
   ↓
return extraction response (unchanged)


Important:

cleaning does NOT affect API response

cleaning failure does NOT block upload

extraction and cleaning are separate stages

both artifacts must exist on disk

6. Why Two Files Are Required (IMPORTANT)

This is intentional.

File	Purpose
extraction/<doc_id>.json	audit, debugging, reprocessing
cleaned/<doc_id>.json	chunking, embedding, retrieval

This is bank-grade design.

7. What We Are NOT Doing Yet (IMPORTANT)

Do NOT implement:

chunking

embeddings

retriever

reranker

graph RAG

generation

evaluation

Those come next.

8. Known Limitations (ACCEPTED)

image description generation still unstable

charts sometimes detected as text

some tables are imperfect

OCR not always needed

performance not fully optimized yet

This is fine at ingestion stage.

9. Next Phase (AFTER THIS FILE)

Once ingestion is stable:

CLEANED TEXT → CHUNKING → EMBEDDING → RETRIEVAL


Chunking will:

operate on cleaned pages

preserve metadata

fix multi-doc accuracy drop

10. Engineering Rules (NON-NEGOTIABLE)

GLM must:

read this file fully

not refactor existing logic

not change endpoints

not break schemas

not move files

ask if unclear

follow specs exactly

This is a shared understanding contract.

11. Current Status Summary
Layer	Status
Upload	✅ Done
Extraction	✅ Stable
Persistence	✅ Done
Cleaning	✅ Implemented
Image LLM	⚠️ Partial
Chunking	⏳ Next
Embeddings	⏳ Next
Retrieval	⏳ Next
Generation	⏳ Next
12. Final Note

We are building this step by step, correctly.

No shortcuts.
No hacks.
No “just make it work”.

This is how production RAG systems are built.

✅ End of file