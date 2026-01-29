"""
Multi-Tenant Collection API Routes
===================================

WHAT IS THIS MODULE?
--------------------
This module provides API endpoints for managing multi-tenant Qdrant collections.
Each tenant gets their own isolated collection in the vector database.

MULTI-TENANT ARCHITECTURE:
--------------------------
- Each tenant has a unique collection_id
- Collections are named: rag_<collection_id>
- Tenants can ingest, query, and delete their own collections
- Existing /query and /api/v1/ingest endpoints continue to work with default collection

NEW ENDPOINTS:
--------------
1. POST /api/v1/collections/create - Create a new tenant collection
2. POST /api/v1/collections/{collection_id}/ingest - Ingest into specific collection
3. POST /api/v1/collections/{collection_id}/query - Query from specific collection
4. DELETE /api/v1/collections/{collection_id} - Delete a collection

BACKWARD COMPATIBILITY:
-----------------------
- Existing /query endpoint uses default collection
- Existing /api/v1/ingest endpoint uses default collection
- No breaking changes to existing behavior
"""

import os
import tempfile
import shutil
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, Path

# Import schemas
from src.api.schemas.requests import CreateCollectionRequest, QueryRequest
from src.api.schemas.responses import (
    CreateCollectionResponse,
    DeleteCollectionResponse,
    QueryResponse
)
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
    prefix="/api/v1/collections",
    tags=["collections"]
)

# Cache for collection-specific services
# {collection_id: {"vector_store": ..., "ingestion_service": ..., "rag_pipeline": ...}}
_collection_services: dict = {}


def _get_collection_name(collection_id: str) -> str:
    """
    Convert collection_id to full Qdrant collection name.

    Args:
        collection_id: The tenant's collection ID

    Returns:
        Full collection name in format: rag_<collection_id>
    """
    return f"rag_{collection_id}"


def _get_vector_store_for_collection(collection_id: str):
    """
    Get or create a vector store instance for the specific collection.

    This creates a new QdrantVectorStore instance targeting the
    tenant's specific collection. The instance is cached for reuse.

    Args:
        collection_id: The tenant's collection ID

    Returns:
        A VectorStoreProvider instance for the tenant's collection
    """
    global _collection_services

    if collection_id not in _collection_services:
        # Create a new vector store instance for this collection
        collection_name = _get_collection_name(collection_id)

        print(f"[Collections] Creating vector store for collection: {collection_name}")

        vector_store = create_vector_store_provider(
            provider=settings.vector_store_provider,
            collection_name=collection_name,
            vector_dimension=settings.vector_dimension
        )

        # Cache the vector store
        _collection_services[collection_id] = {
            "vector_store": vector_store,
            "ingestion_service": None,
            "rag_pipeline": None
        }

    return _collection_services[collection_id]["vector_store"]


def _get_ingestion_service_for_collection(collection_id: str) -> IngestionService:
    """
    Get or create an ingestion service for the specific collection.

    This creates a new IngestionService that uses the tenant's
    specific vector store.

    Args:
        collection_id: The tenant's collection ID

    Returns:
        An IngestionService instance for the tenant's collection
    """
    global _collection_services

    if collection_id not in _collection_services:
        _get_vector_store_for_collection(collection_id)

    if _collection_services[collection_id]["ingestion_service"] is None:
        # Get the collection's vector store
        vector_store = _collection_services[collection_id]["vector_store"]

        # Get shared embedding provider
        embedding_provider = get_embedding_provider()

        # Create ingestion service with the collection's vector store
        _collection_services[collection_id]["ingestion_service"] = IngestionService(
            embedding_provider=embedding_provider,
            vector_store=vector_store
        )

    return _collection_services[collection_id]["ingestion_service"]


def _get_rag_pipeline_for_collection(collection_id: str) -> RAGPipeline:
    """
    Get or create a RAG pipeline for the specific collection.

    This creates a new RAGPipeline that uses the tenant's
    specific vector store.

    Args:
        collection_id: The tenant's collection ID

    Returns:
        An RAGPipeline instance for the tenant's collection
    """
    global _collection_services

    if collection_id not in _collection_services:
        _get_vector_store_for_collection(collection_id)

    if _collection_services[collection_id]["rag_pipeline"] is None:
        # Get the collection's vector store
        vector_store = _collection_services[collection_id]["vector_store"]

        # Get shared providers
        embedding_provider = get_embedding_provider()
        llm_provider = get_llm_provider()
        reranker_provider = get_reranker()

        # Create RAG pipeline with the collection's vector store
        _collection_services[collection_id]["rag_pipeline"] = RAGPipeline(
            embedding_provider=embedding_provider,
            vector_store_provider=vector_store,
            llm_provider=llm_provider,
            reranker_provider=reranker_provider
        )

    return _collection_services[collection_id]["rag_pipeline"]


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/create",
    response_model=CreateCollectionResponse,
    summary="Create a new collection",
    description="""
    Creates a new Qdrant collection for a tenant.

    The collection will be named: rag_<collection_id>

    This operation is idempotent - if the collection already exists,
    it returns success without modifying it.
    """
)
async def create_collection(request: CreateCollectionRequest) -> CreateCollectionResponse:
    """
    Create a new multi-tenant collection.

    Args:
        request: Request containing the collection_id

    Returns:
        CreateCollectionResponse with success status and collection details

    Example:
        POST /api/v1/collections/create
        {
            "collection_id": "client123"
        }
    """
    try:
        collection_name = _get_collection_name(request.collection_id)

        print(f"\n[Collections] Creating collection: {collection_name}")

        # Create a vector store instance for this collection
        # This will automatically create collection if it doesn't exist
        vector_store = _get_vector_store_for_collection(request.collection_id)

        # Collection is created during vector store initialization
        # No additional verification needed - if we got here, it worked
        print(f"[Collections] Collection ready: {collection_name}")

        return CreateCollectionResponse(
            success=True,
            message="Collection created successfully",
            collection_name=collection_name,
            collection_id=request.collection_id
        )

    except Exception as e:
        print(f"[Collections] ERROR creating collection: {str(e)}")
        return CreateCollectionResponse(
            success=False,
            message=f"Failed to create collection: {str(e)}",
            collection_name=_get_collection_name(request.collection_id),
            collection_id=request.collection_id
        )


@router.post(
    "/{collection_id}/ingest",
    response_model=IngestResponse,
    summary="Ingest documents into a collection",
    description="""
    Ingest one or more documents into the specified tenant's collection.

    Multiple files can be uploaded at once. Each file is processed
    independently using the existing ingestion pipeline.

    Document Tracking:
    - Each chunk includes file_name and document_id in metadata
    - Queries can identify which document each chunk came from
    """
)
async def ingest_into_collection(
    collection_id: str = Path(..., description="The collection ID", min_length=1, max_length=100),
    files: List[UploadFile] = File(..., description="Document files to ingest (multiple)")
) -> IngestResponse:
    """
    Ingest multiple documents into a specific tenant collection.

    Args:
        collection_id: The tenant's collection ID
        files: List of document files to ingest

    Returns:
        IngestResponse with aggregated results

    Example:
        POST /api/v1/collections/client123/ingest
        (multipart/form-data with multiple files)
    """
    # Validate files
    if not files or len(files) == 0:
        return IngestResponse(
            success=False,
            message="No files provided",
            error="At least one file is required"
        )

    print(f"\n{'='*80}")
    print(f"[Collections] BATCH INGESTION: {collection_id}")
    print(f"[Collections] Files to process: {len(files)}")
    print(f"{'='*80}")

    # Get the ingestion service for this collection
    try:
        service = _get_ingestion_service_for_collection(collection_id)
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
    first_file_name = files[0].filename if files else ""

    for idx, file in enumerate(files, 1):
        print(f"\n[Collections] Processing file {idx}/{len(files)}: {file.filename}")

        # Validate file
        if not file.filename:
            print(f"[Collections]   ✗ Skipped: No filename")
            failed_files += 1
            continue

        # Check if file type is supported
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in service.get_supported_extensions():
            print(f"[Collections]   ✗ Skipped: Unsupported file type '{ext}'")
            failed_files += 1
            continue

        # Save file temporarily
        temp_dir = None
        temp_path = None

        try:
            temp_dir = tempfile.mkdtemp(prefix="rag_ingest_")
            temp_path = os.path.join(temp_dir, file.filename)

            # Read and save file
            with open(temp_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)

            print(f"[Collections]   ✓ Loaded {os.path.getsize(temp_path)} bytes")

            # Ingest file
            result = service.ingest_file(temp_path)

            if result.success:
                total_chunks += result.chunk_count
                successful_files += 1
                print(f"[Collections]   ✓ Created {result.chunk_count} chunks")
                print(f"[Collections]   ✓ Stored in rag_{collection_id}")
            else:
                failed_files += 1
                print(f"[Collections]   ✗ Failed: {result.error}")

        except Exception as e:
            failed_files += 1
            print(f"[Collections]   ✗ Error: {str(e)}")

        finally:
            # Cleanup temp file
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"[Collections]   Warning: Could not clean up temp dir: {e}")

    # Print summary
    print(f"\n{'='*80}")
    print(f"[Collections] BATCH INGESTION COMPLETE")
    print(f"[Collections] Total files: {len(files)}")
    print(f"[Collections] Successful: {successful_files}")
    print(f"[Collections] Failed: {failed_files}")
    print(f"[Collections] Total chunks stored: {total_chunks}")
    print(f"{'='*80}\n")

    # Return aggregated result
    if successful_files > 0:
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {successful_files} document(s)",
            document_name=f"{successful_files} file(s) processed",
            document_id="multiple",
            chunk_count=total_chunks,
            metadata={
                "files_processed": successful_files,
                "total_chunks": total_chunks,
                "collection_id": collection_id,
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
    "/{collection_id}/query",
    response_model=QueryResponse,
    summary="Query a collection",
    description="""
    Query the specified tenant's collection.

    Reuses the existing RAG pipeline (embed, retrieve, rerank, generate)
    but searches in the tenant's isolated collection.
    """
)
async def query_collection(
    collection_id: str = Path(..., description="The collection ID", min_length=1, max_length=100),
    request: QueryRequest = None
) -> QueryResponse:
    """
    Query a specific tenant collection.

    Args:
        collection_id: The tenant's collection ID
        request: QueryRequest with the question

    Returns:
        QueryResponse with answer and sources

    Example:
        POST /api/v1/collections/client123/query
        {
            "question": "What is RAG?"
        }
    """
    print(f"\n[Collections] Querying collection: {collection_id}")

    if request is None:
        raise HTTPException(
            status_code=400,
            detail="Request body is required. Please provide a 'question' field."
        )

    try:
        question = request.question
        print(f"[Collections] Question: {question[:100]}...")

        # Get the RAG pipeline for this collection
        pipeline = _get_rag_pipeline_for_collection(collection_id)

        # Run the query
        result = pipeline.run(question=question)

        print(f"[Collections] Generated answer with {len(result['sources'])} sources")

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )

    except Exception as e:
        print(f"[Collections] Query ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your query: {str(e)}"
        )


@router.delete(
    "/{collection_id}",
    response_model=DeleteCollectionResponse,
    summary="Delete a collection",
    description="""
    Delete the specified tenant's collection from Qdrant.

    This operation is idempotent - if the collection doesn't exist,
    it returns success without error.

    WARNING: This permanently deletes all data in the collection.
    """
)
async def delete_collection(
    collection_id: str = Path(..., description="The collection ID", min_length=1, max_length=100)
) -> DeleteCollectionResponse:
    """
    Delete a tenant collection.

    Args:
        collection_id: The tenant's collection ID

    Returns:
        DeleteCollectionResponse with success status

    Example:
        DELETE /api/v1/collections/client123
    """
    try:
        collection_name = _get_collection_name(collection_id)

        print(f"\n[Collections] Deleting collection: {collection_name}")

        # Get the vector store for this collection and call delete_collection
        try:
            vector_store = _get_vector_store_for_collection(collection_id)
            success = vector_store.delete_collection()

            if success:
                # Remove from cache
                global _collection_services
                if collection_id in _collection_services:
                    del _collection_services[collection_id]

                return DeleteCollectionResponse(
                    success=True,
                    message="Collection deleted successfully",
                    collection_id=collection_id
                )
            else:
                return DeleteCollectionResponse(
                    success=False,
                    message="Failed to delete collection",
                    collection_id=collection_id
                )

        except Exception as e:
            return DeleteCollectionResponse(
                success=False,
                message=f"Error: {str(e)}",
                collection_id=collection_id
            )

    except Exception as e:
        print(f"[Collections] Delete ERROR: {str(e)}")
        # Even on error, we return idempotent success
        return DeleteCollectionResponse(
            success=True,
            message=f"Collection delete attempted: {str(e)}",
            collection_id=collection_id
        )
