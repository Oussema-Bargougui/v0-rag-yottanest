# Chat Endpoints Implementation Guide

## 🎯 Objective
Create 2 new endpoints for session-based chat with multi-document upload support.

## 📋 Endpoints to Create

### Endpoint 1: `POST /api/v1/chat/ingest`
- Upload multiple documents to a session-based collection
- Session-based: same session_id = same collection
- Multi-document upload: accept List[UploadFile]
- Creates collection if needed, reuses if exists

### Endpoint 2: `POST /api/v1/chat/query`
- Query documents in a session collection using RAG
- Searches across ALL documents in the session
- Returns answer with sources showing which document each chunk came from

---

## ✅ Requirements

1. **Multi-document upload** - Accept List[UploadFile]
2. **Session-based collections** - Each session_id = isolated collection (rag_{collection_id})
3. **Reuse collections** - Same session_id always uses same collection
4. **Clear logging** - Show progress for each file
5. **Document tracking** - Each chunk has file_name and document_id (already works!)
6. **NO logic changes** - Keep extraction, chunking, embedding, storage exactly the same
7. **Reuse existing services** - Use IngestionService and RAGPipeline

---

## 📁 File to Create

**File:** `src/api/routes/chat.py`

**New file** - create from scratch

---

## 🔧 Implementation Steps

### Step 1: Create New Route File

Create `src/api/routes/chat.py` with the following content:

```python
"""
Chat Endpoints for Session-Based Multi-Document Upload
====================================================

WHAT ARE THESE ENDPOINTS?
-------------------------
These endpoints provide a simplified chat interface for uploading
and querying documents in session-based collections.

ENDPOINTS:
---------
1. POST /api/v1/chat/ingest - Upload multiple documents to a session
2. POST /api/v1/chat/query - Query documents in a session

SESSION-BEHAVIOR:
-----------------
- Each session_id maps to a unique Qdrant collection (rag_{session_id})
- Same session_id always uses same collection
- Different session_ids use different collections
- Sessions are isolated from each other

MULTI-DOCUMENT SUPPORT:
-----------------------
- ingest endpoint accepts multiple files at once
- All files are stored in the same session collection
- Query endpoint searches across all documents in the session

DOCUMENT TRACKING:
------------------
- Each chunk includes file_name and document_id in metadata
- Query responses show which document each source came from
"""

import os
import tempfile
import shutil
from typing import List

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Path
from pydantic import BaseModel

# Import schemas
from src.api.schemas.requests import QueryRequest
from src.api.schemas.responses import QueryResponse
from src.api.routes.ingest import IngestResponse

# Import services and providers
from src.ingestion.service import IngestionService
from src.rag.pipeline import RAGPipeline
from src.core.config import settings
from src.core.providers import get_embedding_provider, get_llm_provider, get_reranker
from src.vectorstore.factory import create_vector_store_provider


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"]
)

# Cache for session-specific services
# {session_id: {"vector_store": ..., "ingestion_service": ..., "rag_pipeline": ...}}
_session_services: dict = {}


def _get_collection_name(session_id: str) -> str:
    """
    Convert session_id to full Qdrant collection name.

    Args:
        session_id: The session ID

    Returns:
        Full collection name in format: rag_{session_id}
    """
    return f"rag_{session_id}"


def _get_vector_store_for_session(session_id: str):
    """
    Get or create a vector store instance for the specific session.

    This creates a new QdrantVectorStore instance targeting the
    session's specific collection. The instance is cached for reuse.

    Args:
        session_id: The session ID

    Returns:
        A VectorStoreProvider instance for the session's collection
    """
    global _session_services

    if session_id not in _session_services:
        # Create a new vector store instance for this session
        collection_name = _get_collection_name(session_id)

        print(f"[Chat] Creating vector store for session: {session_id}")
        print(f"[Chat] Collection name: {collection_name}")

        vector_store = create_vector_store_provider(
            provider=settings.vector_store_provider,
            collection_name=collection_name,
            vector_dimension=settings.vector_dimension
        )

        # Cache the vector store
        _session_services[session_id] = {
            "vector_store": vector_store,
            "ingestion_service": None,
            "rag_pipeline": None
        }

    return _session_services[session_id]["vector_store"]


def _get_ingestion_service_for_session(session_id: str) -> IngestionService:
    """
    Get or create an ingestion service for the specific session.

    This creates a new IngestionService that uses the session's
    specific vector store.

    Args:
        session_id: The session ID

    Returns:
        An IngestionService instance for the session's collection
    """
    global _session_services

    if session_id not in _session_services:
        _get_vector_store_for_session(session_id)

    if _session_services[session_id]["ingestion_service"] is None:
        # Get the session's vector store
        vector_store = _session_services[session_id]["vector_store"]

        # Get shared embedding provider
        embedding_provider = get_embedding_provider()

        # Create ingestion service with the session's vector store
        _session_services[session_id]["ingestion_service"] = IngestionService(
            embedding_provider=embedding_provider,
            vector_store=vector_store
        )

    return _session_services[session_id]["ingestion_service"]


def _get_rag_pipeline_for_session(session_id: str) -> RAGPipeline:
    """
    Get or create a RAG pipeline for the specific session.

    This creates a new RAGPipeline that uses the session's
    specific vector store.

    Args:
        session_id: The session ID

    Returns:
        An RAGPipeline instance for the session's collection
    """
    global _session_services

    if session_id not in _session_services:
        _get_vector_store_for_session(session_id)

    if _session_services[session_id]["rag_pipeline"] is None:
        # Get the session's vector store
        vector_store = _session_services[session_id]["vector_store"]

        # Get shared providers
        embedding_provider = get_embedding_provider()
        llm_provider = get_llm_provider()
        reranker_provider = get_reranker()

        # Create RAG pipeline with the session's vector store
        _session_services[session_id]["rag_pipeline"] = RAGPipeline(
            embedding_provider=embedding_provider,
            vector_store_provider=vector_store,
            llm_provider=llm_provider,
            reranker_provider=reranker_provider
        )

    return _session_services[session_id]["rag_pipeline"]


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Upload documents to chat session",
    description="""
    Upload one or more documents to a session-based collection.

    Multi-Document Support:
    - Multiple files can be uploaded at once
    - All files are stored in the same session collection
    - Each file is processed independently using existing ingestion pipeline

    Session Behavior:
    - Same session_id always uses the same collection (rag_{session_id})
    - Collection is created on first upload
    - Subsequent uploads reuse the same collection
    - Different session_ids use different isolated collections

    Document Tracking:
    - Each chunk includes file_name and document_id in metadata
    - Query responses can identify which document each chunk came from
    """
)
async def chat_ingest(
    session_id: str = Form(..., description="Session ID for this chat"),
    files: List[UploadFile] = File(..., description="Document files to upload (multiple)"),
    description: str = Form(default="", description="Optional session description")
) -> IngestResponse:
    """
    Ingest multiple documents into a session-based collection.

    Args:
        session_id: The session ID (e.g., "session_abc123")
        files: List of document files to ingest
        description: Optional session description

    Returns:
        IngestResponse with aggregated results

    Example:
        POST /api/v1/chat/ingest
        session_id: "session_abc123"
        files: [doc1.pdf, doc2.pdf, doc3.pdf]
    """
    # Validate session_id
    if not session_id or not session_id.strip():
        return IngestResponse(
            success=False,
            message="No session ID provided",
            error="Session ID is required"
        )

    # Validate files
    if not files or len(files) == 0:
        return IngestResponse(
            success=False,
            message="No files provided",
            error="At least one file is required"
        )

    print(f"\n{'='*80}")
    print(f"[Chat] CHAT INGESTION: {session_id}")
    print(f"[Chat] Files to process: {len(files)}")
    if description:
        print(f"[Chat] Description: {description}")
    print(f"{'='*80}")

    # Get the ingestion service for this session
    try:
        service = _get_ingestion_service_for_session(session_id)
    except Exception as e:
        return IngestResponse(
            success=False,
            message="Ingestion service unavailable",
            document_name=f"{len(files)} files",
            error=f"Could not initialize ingestion service: {str(e)}"
        )

    # Process each file
    total_chunks = 0
    successful_files = 0
    failed_files = 0

    for idx, file in enumerate(files, 1):
        print(f"\n[Chat] Processing file {idx}/{len(files)}: {file.filename}")

        # Validate file
        if not file.filename:
            print(f"[Chat]   ✗ Skipped: No filename")
            failed_files += 1
            continue

        # Check if file type is supported
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in service.get_supported_extensions():
            print(f"[Chat]   ✗ Skipped: Unsupported file type '{ext}'")
            failed_files += 1
            continue

        # Save file temporarily
        temp_dir = None
        temp_path = None

        try:
            temp_dir = tempfile.mkdtemp(prefix="chat_ingest_")
            temp_path = os.path.join(temp_dir, file.filename)

            # Read and save file
            with open(temp_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)

            print(f"[Chat]   ✓ Loaded {os.path.getsize(temp_path)} bytes")

            # Ingest the file
            result = service.ingest_file(temp_path)

            if result.success:
                total_chunks += result.chunk_count
                successful_files += 1
                print(f"[Chat]   ✓ Created {result.chunk_count} chunks")
                print(f"[Chat]   ✓ Stored in rag_{session_id}")
            else:
                failed_files += 1
                print(f"[Chat]   ✗ Failed: {result.error}")

        except Exception as e:
            failed_files += 1
            print(f"[Chat]   ✗ Error: {str(e)}")

        finally:
            # Cleanup temp file
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"[Chat]   Warning: Could not clean up temp dir: {e}")

    # Print summary
    print(f"\n{'='*80}")
    print(f"[Chat] CHAT INGESTION COMPLETE")
    print(f"[Chat] Session ID: {session_id}")
    print(f"[Chat] Total files: {len(files)}")
    print(f"[Chat] Successful: {successful_files}")
    print(f"[Chat] Failed: {failed_files}")
    print(f"[Chat] Total chunks stored: {total_chunks}")
    print(f"[Chat] Collection: rag_{session_id}")
    print(f"{'='*80}\n")

    # Return aggregated result
    if successful_files > 0:
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {successful_files} document(s)",
            document_name=f"{successful_files} file(s) processed",
            document_id=session_id,
            chunk_count=total_chunks,
            metadata={
                "session_id": session_id,
                "qdrant_collection": _get_collection_name(session_id),
                "files_processed": successful_files,
                "total_chunks": total_chunks,
                "failed_files": failed_files
            }
        )
    else:
        return IngestResponse(
            success=False,
            message="Failed to ingest any documents",
            document_name=f"{len(files)} files",
            error="All files failed to process"
        )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query chat session",
    description="""
    Query documents in a session collection using RAG.

    This endpoint searches across ALL documents uploaded to the session
    and returns an AI-generated answer with relevant sources.

    Document Tracking:
    - Response includes sources with file_name for each chunk
    - You can identify which document each source came from
    - Includes relevance scores for ranking

    Session Behavior:
    - Queries only the specified session's collection
    - Different sessions are completely isolated
    """
)
async def chat_query(
    session_id: str = Form(..., description="Session ID to query"),
    query: str = Form(..., description="Question to ask"),
    top_k: int = Form(default=5, description="Number of relevant chunks to retrieve")
) -> QueryResponse:
    """
    Query a session's documents.

    Args:
        session_id: The session ID to query
        query: The question to ask
        top_k: Number of relevant chunks to retrieve

    Returns:
        QueryResponse with answer and sources

    Example:
        POST /api/v1/chat/query
        session_id: "session_abc123"
        query: "What is the main topic?"
        top_k: 5
    """
    print(f"\n{'='*80}")
    print(f"[Chat] CHAT QUERY: {session_id}")
    print(f"[Chat] Query: {query[:100]}{'...' if len(query) > 100 else ''}")
    print(f"[Chat] Top K: {top_k}")
    print(f"{'='*80}")

    # Validate session_id
    if not session_id or not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID is required"
        )

    # Validate query
    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query is required"
        )

    try:
        # Get the RAG pipeline for this session
        pipeline = _get_rag_pipeline_for_session(session_id)

        # Run the query
        result = pipeline.run(question=query, top_k=top_k)

        print(f"[Chat] Generated answer with {len(result['sources'])} sources")
        print(f"[Chat] Query completed in {result.get('query_time_ms', 0)}ms")

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            query_time_ms=result.get("query_time_ms", 0)
        )

    except Exception as e:
        print(f"[Chat] Query ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your query: {str(e)}"
        )
```

---

## 🔧 Step 2: Register the New Router

Update `src/api/app.py` to include the new chat router:

Add this import:
```python
from src.api.routes import chat
```

Add this line with the other router inclusions:
```python
app.include_router(chat.router)
```

---

## 📊 Expected Log Output

### Upload 3 Documents:

```
================================================================================
[Chat] CHAT INGESTION: session_abc123
[Chat] Files to process: 3
[Chat] Description: Research session
================================================================================

[Chat] Processing file 1/3: paper1.pdf
[Chat]   ✓ Loaded 25000 bytes
[Chat]   ✓ Created 150 chunks
[Chat]   ✓ Stored in rag_session_abc123

[Chat] Processing file 2/3: paper2.pdf
[Chat]   ✓ Loaded 30000 bytes
[Chat]   ✓ Created 200 chunks
[Chat]   ✓ Stored in rag_session_abc123

[Chat] Processing file 3/3: notes.txt
[Chat]   ✓ Loaded 5000 bytes
[Chat]   ✓ Created 50 chunks
[Chat]   ✓ Stored in rag_session_abc123

================================================================================
[Chat] CHAT INGESTION COMPLETE
[Chat] Session ID: session_abc123
[Chat] Total files: 3
[Chat] Successful: 3
[Chat] Failed: 0
[Chat] Total chunks stored: 400
[Chat] Collection: rag_session_abc123
================================================================================
```

### Query Session:

```
================================================================================
[Chat] CHAT QUERY: session_abc123
[Chat] Query: What is the main topic?
[Chat] Top K: 5
================================================================================
[Chat] Generated answer with 5 sources
[Chat] Query completed in 2340ms
```

---

## 📤 Expected Responses

### Ingest Response:

```json
{
  "success": true,
  "message": "Successfully ingested 3 document(s)",
  "document_name": "3 file(s) processed",
  "document_id": "session_abc123",
  "chunk_count": 400,
  "metadata": {
    "session_id": "session_abc123",
    "qdrant_collection": "rag_session_abc123",
    "files_processed": 3,
    "total_chunks": 400,
    "failed_files": 0
  }
}
```

### Query Response:

```json
{
  "answer": "Based on your documents, the main topic is...",
  "sources": [
    {
      "file_name": "paper1.pdf",
      "chunk_id": "doc_paper1.pdf_chunk_15",
      "text": "...relevant chunk text...",
      "score": 0.95
    },
    {
      "file_name": "paper2.pdf",
      "chunk_id": "doc_paper2.pdf_chunk_8",
      "text": "...relevant chunk text...",
      "score": 0.87
    }
  ],
  "query_time_ms": 2340
}
```

---

## 🧪 Testing via Swagger UI

### Test 1: Upload Documents

1. Start the service:
   ```bash
   python main.py
   ```

2. Open Swagger UI:
   ```
   http://localhost:8001/docs
   ```

3. Find the endpoint:
   ```
   POST /api/v1/chat/ingest
   ```

4. Click "Try it out"

5. Fill in:
   - `session_id`: `session_abc123`
   - `description`: `My research session` (optional)

6. In the "files" parameter:
   - Click "Choose File"
   - Select multiple files (paper1.pdf, paper2.pdf, notes.txt)
   - You can select multiple files in the file dialog

7. Click "Execute"

8. View the response and logs

### Test 2: Upload More Documents (Same Session)

1. Same endpoint: `POST /api/v1/chat/ingest`

2. Use same `session_id`: `session_abc123`

3. Upload more files

4. Verify they're added to same collection (total chunks increases)

### Test 3: Query Session

1. Find the endpoint:
   ```
   POST /api/v1/chat/query
   ```

2. Click "Try it out"

3. Fill in:
   - `session_id`: `session_abc123`
   - `query`: `What is the main topic?`
   - `top_k`: `5`

4. Click "Execute"

5. View the response - should show answer with sources from multiple documents

### Test 4: Different Session

1. Upload to new session_id: `session_xyz789`

2. Query new session - should only see documents from that session

3. Old session should still work independently

---

## ✅ Verification Checklist

- [ ] Created `src/api/routes/chat.py`
- [ ] Added import to `src/api/app.py`
- [ ] Registered router in `src/api/app.py`
- [ ] Endpoint 1 accepts multiple files
- [ ] Endpoint 1 creates collection on first upload
- [ ] Endpoint 1 reuses collection for same session_id
- [ ] Logs show clear progress for each file
- [ ] Response shows aggregated chunk count
- [ ] Document tracking works (file_name and document_id)
- [ ] Endpoint 2 queries specific session
- [ ] Endpoint 2 returns answer with sources
- [ ] Sources show which document each chunk came from
- [ ] Different sessions are isolated
- [ ] Extraction logic unchanged
- [ ] Chunking logic unchanged
- [ ] Embedding logic unchanged
- [ ] Storage logic unchanged

---

## 🎯 Session Behavior Examples

### Session 1:
```
POST /api/v1/chat/ingest
session_id: "session_abc123"
files: [doc1.pdf, doc2.pdf]
→ Creates: rag_session_abc123
→ Stores: 350 chunks

POST /api/v1/chat/ingest
session_id: "session_abc123"
files: [doc3.pdf, doc4.pdf]
→ Uses: rag_session_abc123 (existing)
→ Adds: 400 more chunks
→ Total: 750 chunks

POST /api/v1/chat/query
session_id: "session_abc123"
query: "What is...?"
→ Searches: All 750 chunks
→ Returns: Answer + sources from any of 4 documents
```

### Session 2:
```
POST /api/v1/chat/ingest
session_id: "session_xyz789"
files: [doc5.pdf]
→ Creates: rag_session_xyz789 (NEW collection)
→ Stores: 150 chunks

POST /api/v1/chat/query
session_id: "session_xyz789"
query: "What is...?"
→ Searches: Only 150 chunks (doc5.pdf only)
→ Returns: Answer + sources from doc5.pdf only
```

---

## 📝 Important Notes

1. **Do NOT change** `IngestionService` - it already handles everything correctly
2. **Do NOT change** `RAGPipeline` - it already handles everything correctly
3. **Do NOT change** chunking, embedding, or storage logic
4. **Only create** the new route file and endpoints
5. **Document tracking** is automatic - each chunk has metadata:
   - `file_name`: Original filename
   - `document_id`: Unique ID for the document
   - `chunk_id`: Unique ID for the chunk
6. **Session isolation** - each session_id = isolated collection
7. **Error handling** - if one file fails, continue with others
8. **No detailed summary** - just aggregated counts

---

## 🚨 If Something Goes Wrong

1. Check logs - they should show which file failed and why
2. Verify file types are supported (PDF, TXT, HTML, DOCX)
3. Check Qdrant connection
4. Verify collections are created: `rag_{session_id}`
5. Ensure session_id is passed correctly to both endpoints
6. Check that router is registered in `src/api/app.py`

---

## 🎉 Success Indicators

✅ Can upload 5+ files at once  
✅ Same session_id uses same collection  
✅ Different session_ids use different collections  
✅ All chunks stored in session collection  
✅ Logs show clear progress for each file  
✅ Response shows total chunks across all files  
✅ Query returns answers from multiple documents  
✅ Each source in response shows correct file name  
✅ Sessions are completely isolated  
✅ NO existing logic broken