# RAG Ingestion Refactor – LangChain-Based Data Loader (Production Design)

## 1. Purpose

This document defines the **new ingestion and extraction pipeline** for the RAG system.

We are refactoring **ONLY the data loader** to use **LangChain document loaders** in order to:
- improve extraction quality
- remove layout noise
- speed up ingestion
- handle multiple formats reliably
- improve downstream chunking & retrieval accuracy
- support multi-document uploads (batch / folder)

⚠️ This document applies ONLY to the ingestion stage.  
RAG chunking, embeddings, retrieval, generation, API, and frontend MUST NOT be modified.

---

## 2. Core Decision

We will use **LangChain loaders (Unstructured-based)** to handle extraction.

### Why:
- PDF parsing is hard and already solved
- Layout-based extraction is bad for RAG
- We want clean, compact, linear text
- We want tables as text, not objects
- We want images injected into text, not stored separately
- We want consistent metadata across formats

LangChain is used **ONLY as an extraction tool**, not as a RAG framework.

---

## 3. Scope (VERY IMPORTANT)

### We WILL use LangChain for:
- text extraction
- table extraction (as text)
- image caption extraction
- metadata extraction
- multi-format support
- batch ingestion

### We will NOT use LangChain for:
- chunking
- embeddings
- vector DB
- retrieval
- generation
- orchestration
- FastAPI routing
- persistence logic
- evaluation
- monitoring

LangChain = **tool**, not architecture.

---

## 4. Supported File Types

| Format | Loader |
|------|--------|
| PDF | `UnstructuredPDFLoader(strategy="hi_res")` |
| DOCX | `UnstructuredWordDocumentLoader` |
| TXT | `TextLoader` |
| MD | `UnstructuredMarkdownLoader` |
| HTML (future) | `UnstructuredHTMLLoader` |

---

## 5. New Ingestion Pipeline (RAG-FIRST)

### Old (WRONG for RAG)
PDF → blocks → bbox → layout → noise → slow → bad chunks

shell
Copier le code

### New (CORRECT for RAG)
File → LangChain Loader → clean text → chunking → embeddings

yaml
Copier le code

---

## 6. Extraction Rules (MANDATORY)

### 6.1 Text Extraction
- Extract text in reading order
- Merge broken lines
- Remove layout noise
- Remove extra newlines
- Fix hyphenation
- Collapse whitespace
- Ignore font size
- Ignore columns
- Ignore bounding boxes
- Ignore blocks

Output = **clean, compact, linear text**

---

### 6.2 Table Handling
- Detect ONLY real tables (grid, headers, rows)
- Ignore fake layout tables
- Convert tables to text
- Inject tables inline into page text

Example:
TABLE:
Country | Risk Level | Score
France | Medium | 65
Germany | Low | 22

yaml
Copier le code

Tables must NOT be stored as separate objects.

---

### 6.3 Image Handling
Images are NOT first-class objects.

Rules:
- If image has caption → extract caption
- Inject inline into text:
  [IMAGE: caption text]
- If caption exists but no description → generate description with LLM
- If no caption at all → generate description with LLM
- Inject description inline
- Do NOT store image files for RAG
- Do NOT create image chunks

Images enrich text only.

---

## 7. Output Data Model (FINAL FORMAT)

### Page-level output
```json
{
  "page_number": 12,
  "text": "clean text with tables and images injected",
  "metadata": {
    "has_tables": true,
    "has_images": true,
    "source": "filename.pdf"
  }
}
Document-level output
json
Copier le code
{
  "doc_id": "uuid",
  "filename": "document.pdf",
  "file_type": "pdf",
  "num_pages": 142,
  "pages": [...],
  "full_text": "all pages joined together",
  "ingestion_timestamp": "ISO-8601",
  "extraction_version": "5.0.0"
}
8. How LangChain is Used (Implementation Guide)
8.1 Loader Selection
python
Copier le code
def get_loader(path):
    ext = path.suffix.lower()

    if ext == ".pdf":
        return UnstructuredPDFLoader(path, strategy="hi_res")
    elif ext == ".docx":
        return UnstructuredWordDocumentLoader(path)
    elif ext == ".txt":
        return TextLoader(path)
    elif ext == ".md":
        return UnstructuredMarkdownLoader(path)
    else:
        raise ValueError("Unsupported format")
8.2 Load Documents
python
Copier le code
docs = loader.load()
Each doc is a LangChain Document object:

python
Copier le code
Document(
  page_content="clean text",
  metadata={
    "page_number": 1,
    "source": "file.pdf"
  }
)
8.3 Convert to Final Format
python
Copier le code
pages = []
for doc in docs:
    pages.append({
        "page_number": doc.metadata.get("page_number", 0),
        "text": doc.page_content,
        "metadata": doc.metadata
    })
9. Batch Upload Support
The upload endpoint must accept:

python
Copier le code
files: List[UploadFile]
For each file:

Save temp file

Use LangChain loader

Extract pages

Build final document JSON

Save under storage/extraction/<doc_id>.json

Continue even if one file fails