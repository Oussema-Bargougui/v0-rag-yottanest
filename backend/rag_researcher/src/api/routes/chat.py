"""
Chat Endpoints for Session-Based Multi-Document Upload

These endpoints provide a simplified chat interface for uploading
and querying documents in session-based collections.

ENDPOINTS:
- POST /api/v1/chat/ingest - Upload multiple documents to a session
- POST /api/v1/chat/query - Query documents in a session

SESSION BEHAVIOR:
- Each session_id maps to a unique Qdrant collection (rag_{session_id})
- Same session_id always uses same collection
- Different session_ids use different collections
- Sessions are isolated from each other

MULTI-DOCUMENT SUPPORT:
- ingest endpoint accepts multiple files at once
- All files are stored in the same session collection
- Query endpoint searches across all documents in session

DOCUMENT TRACKING:
- Each chunk includes file_name and document_id in metadata
- Query responses show which document each source came from
"""

import os
import tempfile
import shutil
import uuid
import re
from typing import List, Optional

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

    Sanitizes session_id to ensure it's compatible with Qdrant's
    collection naming requirements:
    - Only alphanumeric characters and underscores allowed
    - Must start with a letter or underscore
    - No spaces or special characters

    Args:
        session_id: The session ID

    Returns:
        Full collection name in format: rag_{sanitized_session_id}
    """
    # Replace any non-alphanumeric characters (except underscore) with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', session_id)

    # Ensure it starts with a letter (Qdrant requirement)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"coll_{sanitized}"

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove trailing underscores
    sanitized = sanitized.rstrip('_')

    # If empty after sanitization, use a default
    if not sanitized:
        sanitized = "collection"

    return f"rag_{sanitized}"


def _get_vector_store_for_session(session_id: str):
    """
    Get or create a vector store instance for specific session.

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
        print(f"[Chat] Vector dimension: {settings.vector_dimension}")
        print(f"[Chat] Provider: {settings.vector_store_provider}")

        try:
            vector_store = create_vector_store_provider(
                provider=settings.vector_store_provider,
                collection_name=collection_name,
                vector_dimension=settings.vector_dimension
            )
            print(f"[Chat] Vector store created successfully")
        except Exception as e:
            print(f"[Chat] ERROR creating vector store: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize vector store for session: {str(e)}"
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
    Get or create an ingestion service for specific session.

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
    Get or create a RAG pipeline for specific session.

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
    - Each file is processed independently using the existing ingestion pipeline

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
    session_id: Optional[str] = Form(None, description="Session ID for this chat (optional, auto-generated if not provided)"),
    files: List[UploadFile] = File(..., description="Document files to upload (multiple)")
) -> IngestResponse:
    """
    Ingest multiple documents into a session-based collection.

    Args:
        session_id: The session ID (optional, auto-generated if not provided)
        files: List of document files to ingest

    Returns:
        IngestResponse with aggregated results including session_id

    Example:
        POST /api/v1/chat/ingest
        session_id: "my_session" (or omit for auto-generated)
        files: [doc1.pdf, doc2.pdf, doc3.pdf]
    """
    # Generate session_id if not provided
    if not session_id or not session_id.strip():
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        print(f"[Chat] Auto-generated session_id: {session_id}")

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

            # Ingest file
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
    - Queries only to the specified session's collection
    - Different sessions are completely isolated
    """
)
async def chat_query(
    session_id: str = Form(..., description="Session ID to query"),
    query: str = Form(..., description="Question to ask")
) -> QueryResponse:
    """
    Query a session's documents.

    Args:
        session_id: The session ID to query
        query: The question to ask

    Returns:
        QueryResponse with answer and sources

    Example:
        POST /api/v1/chat/query
        session_id: "session_abc123"
        query: "What is the main topic?"
    """
    print(f"\n{'='*80}")
    print(f"[Chat] CHAT QUERY: {session_id}")
    print(f"[Chat] Query: {query[:100]}{'...' if len(query) > 100 else ''}")
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
        result = pipeline.run(question=query)

        print(f"[Chat] Generated answer with {len(result.get('sources', []))} sources")

        # Build response with available fields
        sources = result.get("sources", [])
        query_time = result.get("query_time_ms", 0)

        return QueryResponse(
            answer=result.get("answer", "No answer generated"),
            sources=sources,
            query_time_ms=query_time
        )

    except Exception as e:
        print(f"[Chat] Query ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your query: {str(e)}"
        )


# =============================================================================
# Session Management Endpoints
# =============================================================================

@router.get(
    "/sessions",
    summary="List all chat sessions",
    description="""
    List all available chat sessions with their metadata.

    Each session corresponds to a Qdrant collection with the 'rag_' prefix.
    Returns information about documents stored in each session.

    Session Metadata:
    - session_id: The unique session identifier
    - document_count: Number of chunks/documents in the session
    - created_date: When the session was first created
    - name: Optional human-readable name (if set)
    """
)
async def list_sessions():
    """
    List all available chat sessions.

    Returns:
        List of session information dictionaries
    """
    from qdrant_client import QdrantClient

    print(f"\n[Chat] Listing all sessions...")

    try:
        # Create Qdrant client using the same configuration as vector store
        # This ensures we connect to the same Qdrant Cloud instance
        if settings.qdrant_url:
            # Cloud mode
            client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
        elif settings.qdrant_host:
            # Local server mode
            client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
        else:
            # In-memory mode
            client = QdrantClient(":memory:")

        # Get all collections
        collections_response = client.get_collections()
        all_collections = collections_response.collections

        # Filter for chat collections (those starting with 'rag_')
        chat_collections = [
            col for col in all_collections
            if col.name.startswith("rag_")
        ]

        print(f"[Chat] Found {len(chat_collections)} chat sessions")

        # Build session list
        sessions = []
        for collection in chat_collections:
            # Extract session_id from collection name (remove 'rag_' prefix)
            session_id = collection.name[4:] if collection.name.startswith("rag_") else collection.name

            # Get collection info for document count using count() instead of get_collection()
            # get_collection() has pydantic validation issues with Qdrant Cloud response
            doc_count = 0
            created_date = None
            try:
                print(f"[Chat] Getting count for collection: {collection.name}")
                
                # Use count() to get point count - this is more reliable
                count_result = client.count(
                    collection_name=collection.name,
                    exact=True
                )
                doc_count = count_result.count
                print(f"[Chat]   Point count: {doc_count}")
                
                # Try to get created date from collection info (if get_collection works)
                try:
                    collection_info = client.get_collection(collection.name)
                    if hasattr(collection_info, 'config') and hasattr(collection_info.config, 'params'):
                        created_date = collection_info.config.params.get('created_at')
                        if created_date:
                            print(f"[Chat]   created_at: {created_date}")
                except Exception as e:
                    # get_collection fails due to pydantic validation, but count() works
                    print(f"[Chat]   Could not get created_date (get_collection failed): {str(e)}")
                
            except Exception as e:
                print(f"[Chat] ERROR getting collection info for {collection.name}: {str(e)}")

            # Get stored session name from metadata point if available
            session_name = None
            try:
                # Try to retrieve the metadata point
                import uuid as uuid_pkg
                # Convert UUID to STRING for the API call
                metadata_uuid_str = str(uuid_pkg.UUID('00000000-0000-0000-0000-000000000001'))
                print(f"[Chat] Retrieving metadata point: {metadata_uuid_str}")
                
                # Retrieve the point using string ID
                points = client.retrieve(
                    collection_name=collection.name,
                    ids=[metadata_uuid_str]
                )
                
                print(f"[Chat] Retrieved {len(points) if points else 0} points")
                
                if points and len(points) > 0:
                    # Extract session_name from payload
                    payload = points[0].payload
                    print(f"[Chat] Payload: {payload}")
                    if payload and '_type' in payload and payload['_type'] == 'session_metadata':
                        session_name = payload.get('session_name')
                        print(f"[Chat]   Session name: '{session_name}'")
            except Exception as e:
                print(f"[Chat] Warning: Could not retrieve metadata for {collection.name}: {str(e)}")
                pass

            sessions.append({
                "session_id": session_id,
                "collection_name": collection.name,
                "name": session_name,
                "document_count": doc_count,
                "created_date": created_date
            })

        print(f"[Chat] Returning {len(sessions)} sessions")
        return {"sessions": sessions}

    except Exception as e:
        print(f"[Chat] ERROR listing sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.put(
    "/sessions/{session_id}/name",
    summary="Rename session",
    description="""
    Update the human-readable name of a session.

    The session name is stored as a special point in the Qdrant collection.
    """
)
async def rename_session(
    session_id: str = Path(..., description="Session ID to rename"),
    name: str = Form(..., description="New name for the session")
):
    """
    Rename a session by storing its name as metadata.

    Args:
        session_id: The session ID
        name: The new session name

    Returns:
        Success message
    """
    from qdrant_client import QdrantClient, models
    import numpy as np

    print(f"\n[Chat] Renaming session {session_id} to '{name}'")

    try:
        # Get the collection name
        collection_name = _get_collection_name(session_id)
        print(f"[Chat] Collection name: {collection_name}")

        # Create Qdrant client using the same configuration
        if settings.qdrant_url:
            client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
        elif settings.qdrant_host:
            client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
        else:
            client = QdrantClient(":memory:")

        # Check if collection exists
        try:
            collections = client.get_collections().collections
            collection_exists = any(col.name == collection_name for col in collections)
            
            if not collection_exists:
                print(f"[Chat] Collection does not exist: {collection_name}")
                return {
                    "success": False,
                    "message": f"Session '{session_id}' not found",
                    "session_id": session_id
                }
        except Exception as e:
            print(f"[Chat] ERROR checking collection existence: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check session: {str(e)}"
            )

        # Store session name as a special metadata point
        # Use a fixed UUID for the metadata point
        import uuid as uuid_pkg
        metadata_uuid = str(uuid_pkg.UUID('00000000-0000-0000-0000-000000000001'))
        
        metadata_point = models.PointStruct(
            id=metadata_uuid,
            vector=np.zeros(settings.vector_dimension, dtype=np.float32).tolist(),
            payload={
                "session_name": name,
                "_type": "session_metadata"
            }
        )

        try:
            # Upsert the metadata point (creates or updates)
            client.upsert(
                collection_name=collection_name,
                points=[metadata_point]
            )
            print(f"[Chat] Session name stored: '{name}'")
        except Exception as e:
            print(f"[Chat] ERROR storing session name: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store session name: {str(e)}"
            )

        print(f"[Chat] Session renamed successfully")
        return {
            "success": True,
            "message": f"Session renamed to '{name}'",
            "session_id": session_id,
            "name": name
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chat] ERROR renaming session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rename session: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    summary="Delete session",
    description="""
    Delete a session and all its documents.

    WARNING: This permanently deletes the entire Qdrant collection
    and all documents stored in it. This action cannot be undone.

    Also removes the session from the service cache.
    """
)
async def delete_session(
    session_id: str = Path(..., description="Session ID to delete")
):
    """
    Delete a session and its collection.

    Args:
        session_id: The session ID

    Returns:
        Success message
    """
    from qdrant_client import QdrantClient

    print(f"\n[Chat] Deleting session: {session_id}")

    try:
        # Get the collection name
        collection_name = _get_collection_name(session_id)
        print(f"[Chat] Collection name: {collection_name}")

        # Create Qdrant client using the same configuration as vector store
        # This ensures we connect to the same Qdrant Cloud instance
        if settings.qdrant_url:
            # Cloud mode
            client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
        elif settings.qdrant_host:
            # Local server mode
            client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
        else:
            # In-memory mode
            client = QdrantClient(":memory:")

        # Check if collection exists first
        try:
            collections = client.get_collections().collections
            collection_exists = any(col.name == collection_name for col in collections)
            
            if not collection_exists:
                print(f"[Chat] Collection does not exist: {collection_name}")
                return {
                    "success": False,
                    "message": f"Session '{session_id}' not found",
                    "session_id": session_id
                }
        except Exception as e:
            print(f"[Chat] ERROR checking collection existence: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check session: {str(e)}"
            )

        # Delete the collection
        try:
            result = client.delete_collection(collection_name)
            print(f"[Chat] Collection deleted: {collection_name}")
        except Exception as e:
            print(f"[Chat] ERROR deleting collection: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete collection: {str(e)}"
            )

        # Remove from service cache
        global _session_services
        if session_id in _session_services:
            del _session_services[session_id]
            print(f"[Chat] Removed session from cache")

        print(f"[Chat] Session deleted successfully")
        return {
            "success": True,
            "message": f"Session '{session_id}' deleted",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chat] ERROR deleting session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )