"""
RAG Researcher FastAPI Service

Production-grade RAG document processing service with multimodal capabilities.
Provides endpoints for document upload, processing, and health checks.

Author: Yottanest Team
Version: 3.0.0 - Production with Persistence and Batch Upload
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
import os
import uuid
import hashlib
import json
from datetime import datetime

# Import configuration and data loaders
from config import Config
from modules.data_loader import MultimodalDataLoader
from modules.rag_text_cleaner import RAGTextCleaner
from modules.semantic_percentile_chunker import SemanticPercentileChunker
from modules.embedder import DocumentEmbedder, EmbeddingError
from modules.vector_store import VectorStore, VectorStoreError
from modules.retriever import Retriever, RetrieverError
from modules.sparse_index_service import SparseIndexService
from modules.llm_generator import LLMGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# FastAPI Application Configuration
# =============================================================================

app = FastAPI(
    title="Yottanest RAG Researcher API",
    description="Production-grade multimodal RAG document processing pipeline",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# -----------------------------------------------------------------------------
# CORS Configuration
# Allow requests from all origins (for testing and Swagger UI)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # Allow all origins (for testing/Swagger)
    allow_credentials=False,            # Credentials not needed for public endpoints
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)

# =============================================================================
# Pydantic Models (Request/Response Schemas)
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    service: str


class BatchUploadResponse(BaseModel):
    """Response model for batch file upload."""
    batch_id: str
    session_id: str
    documents: List[Dict[str, Any]]
    total_files: int
    successful: int
    failed: int


class DocumentUploadResponse(BaseModel):
    """Response model for document upload processing."""
    success: bool
    doc_id: str
    session_id: str
    filename: str
    pages_processed: int
    text_blocks_count: int
    tables_count: int
    images_count: int
    message: str
    error: Optional[str] = None


class PageInfo(BaseModel):
    """Page information model (RAG-first format)."""
    page_number: int
    text: str
    metadata: Dict[str, Any]


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    source: str
    file_type: str
    created_at: str
    original_filename: str
    file_size: int
    file_hash: str
    ingestion_timestamp: str
    processing_duration: float
    extraction_version: str


class StructuredDocumentResponse(BaseModel):
    """Structured document response model."""
    doc_id: str
    session_id: str
    filename: str
    pages: List[PageInfo]
    metadata: DocumentMetadata
    success: bool
    error: Optional[str] = None


class RAGQueryRequest(BaseModel):
    """Request model for RAG query endpoint."""
    query: str = Field(..., description="User query question")
    session_id: str = Field(..., description="Session ID from upload response")


class RAGQueryResponse(BaseModel):
    """Response model for RAG query endpoint."""
    success: bool
    query: str
    session_id: str
    answer: str
    evidence: str
    limitations: str
    citations: List[str]
    chunks_used: int
    confidence: str
    model: str
    timestamp: str
    error: Optional[str] = None

# =============================================================================
# Helper Functions
# =============================================================================

def get_extraction_storage_path() -> Path:
    """
    Get extraction storage directory path.
    
    Returns:
        Path to extraction storage directory
    """
    extraction_path = Config.get_storage_path() / "extraction"
    extraction_path.mkdir(parents=True, exist_ok=True)
    return extraction_path

def get_chunking_storage_path() -> Path:
    """
    Get chunking storage directory path.
    
    Returns:
        Path to chunks storage directory
    """
    chunks_path = Config.get_storage_path() / "chunks"
    chunks_path.mkdir(parents=True, exist_ok=True)
    return chunks_path

def calculate_file_hash(content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content.
    
    Args:
        content: File content as bytes
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    return hashlib.sha256(content).hexdigest()

def save_extraction_to_disk(doc_id: str, result: Dict[str, Any], filename: str, content: bytes, processing_duration: float) -> str:
    """
    Save extraction result to disk as JSON file.
    
    Args:
        doc_id: Document ID
        result: Full extraction result
        filename: Original filename
        content: File content bytes
        processing_duration: Time taken to process
        
    Returns:
        Path to saved JSON file
    """
    extraction_path = get_extraction_storage_path()
    json_path = extraction_path / f"{doc_id}.json"
    
    # Build extraction record
    extraction_record = {
        "doc_id": doc_id,
        "filename": filename,
        "file_size": len(content),
        "file_hash": calculate_file_hash(content),
        "ingestion_timestamp": datetime.now().isoformat(),
        "processing_duration": processing_duration,
        "extraction_version": "5.0.0",
        "pages": result.get('pages', []),
        "metadata": result.get('metadata', {}),
        "processing_stats": {
            "page_count": len(result.get('pages', [])),
            "total_text_length": result.get('full_text', ''),
            "tables_count": sum(1 for page in result.get('pages', []) if page.get('metadata', {}).get('has_tables', False)),
            "images_count": sum(1 for page in result.get('pages', []) if page.get('metadata', {}).get('has_images', False))
        },
        "warnings": [],
        "errors": []
    }
    
    # Save to disk (do not overwrite existing files)
    if not json_path.exists():
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(extraction_record, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved extraction to disk: {json_path}")
    else:
        logger.warning(f"Extraction file already exists: {json_path} (not overwriting)")
    
    return str(json_path)

def get_file_type_from_filename(filename: str) -> str:
    """
    Determine file type from filename.
    
    Args:
        filename: Original filename (may include MIME type from curl uploads)
        
    Returns:
        File type string ('pdf', 'docx', 'txt', 'md')
    """
    try:
        # Sanitize filename: handle curl uploads with MIME type (e.g., "file.pdf;type=application/pdf")
        # Remove ALL quotes (not just leading/trailing) to handle embedded quotes
        sanitized_filename = filename.split(";")[0].strip()
        sanitized_filename = sanitized_filename.replace('"', '').replace("'", '')
        
        ext = Path(sanitized_filename).suffix.lower()
        
        if ext == '.pdf':
            return 'pdf'
        elif ext == '.docx':
            return 'docx'
        elif ext in ['.txt', '.text']:
            return 'txt'
        elif ext in ['.md', '.markdown']:
            return 'md'
        else:
            return 'unknown'
    except Exception as e:
        logger.error(f"Error determining file type from filename '{filename}': {str(e)}")
        return 'unknown'

def validate_file_size(file_size: int, max_size: int = None) -> bool:
    """
    Validate file size against maximum allowed.
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size (defaults to Config.MAX_FILE_SIZE)
        
    Returns:
        True if file size is acceptable
    """
    if max_size is None:
        max_size = Config.MAX_FILE_SIZE
    
    return file_size <= max_size

def validate_file_type(filename: str, content_type: Optional[str] = None) -> bool:
    """
    Validate if file type is supported.
    
    Args:
        filename: Original filename (may include MIME type from curl uploads)
        content_type: Optional MIME type from upload (e.g., "application/pdf")
        
    Returns:
        True if file type is supported
    """
    file_type = get_file_type_from_filename(filename)
    
    # DEBUG: Log validation details
    logger.info(f"Validating file type: '{file_type}' from filename: '{filename}'")
    logger.info(f"Supported formats: {Config.SUPPORTED_FORMATS}")
    
    # Optional: Validate MIME type if provided
    if content_type:
        # Map common MIME types to file types
        mime_to_type = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'docx',
            'text/plain': 'txt',
            'text/markdown': 'md'
        }
        mime_type = mime_to_type.get(content_type.lower())
        if mime_type and mime_type != file_type:
            logger.warning(f"MIME type '{content_type}' suggests '{mime_type}' but filename suggests '{file_type}'")
    
    # SIMPLIFIED: Check if file_type is in supported formats (with or without dot)
    for supported in Config.SUPPORTED_FORMATS:
        # Normalize both to same format (without leading dot)
        normalized_supported = supported.lstrip('.')
        if file_type == normalized_supported:
            logger.info(f"File type '{file_type}' is supported (matches '{supported}')")
            return True
    
    logger.warning(f"File type '{file_type}' is NOT supported")
    return False

def save_chunks_to_disk(doc_id: str, cleaned_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run semantic percentile chunking and save chunks to disk.
    
    Args:
        doc_id: Document ID
        cleaned_json: Cleaned document JSON
        
    Returns:
        Dictionary with chunking summary (doc_id, document_name, chunk_count, chunks_path)
    """
    try:
        logger.info(f"Starting semantic percentile chunking for {doc_id}")
        
        # Initialize semantic percentile chunker (ONLY strategy used)
        chunker = SemanticPercentileChunker()
        
        # Run semantic percentile chunking - returns LIST of chunks
        chunks = chunker.chunk_document(cleaned_json)
        
        # Enrich metadata for each chunk (AFTER chunking complete)
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            # 1) chunk_size = len(chunk.text)
            chunk["chunk_size"] = len(chunk.get("text", ""))
            
            # 2) chunk_index = index in final chunks list
            chunk["chunk_index"] = i
            
            # 3) total_chunks = total number of chunks
            chunk["total_chunks"] = total_chunks
            
            # 4) section_hint: first line of chunk
            chunk_text = chunk.get("text", "")
            first_line = chunk_text.split('\n')[0] if chunk_text else ""
            
            # If < 120 chars and contains letters, use it (strip bullets)
            if len(first_line) < 120 and any(c.isalpha() for c in first_line):
                # Strip common bullet characters
                section_hint = first_line.strip()
                section_hint = section_hint.lstrip('•-*–—◦▪')
                section_hint = section_hint.strip()
                chunk["section_hint"] = section_hint
            else:
                chunk["section_hint"] = None
        
        # Wrap in dict for storage format
        chunks_dict = {
            "doc_id": doc_id,
            "document_name": cleaned_json.get("document_name", "unknown"),
            "chunk_strategy": "semantic_percentile",
            "chunk_count": len(chunks),
            "chunks": chunks
        }
        
        # Save to: storage/chunks/<doc_id>_chunks.json
        chunks_path = get_chunking_storage_path()
        output_path = chunks_path / f"{doc_id}_chunks.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved chunks: {output_path}")
        
        # Return summary only (no chunk text)
        return {
            "doc_id": doc_id,
            "document_name": cleaned_json.get("document_name", "unknown"),
            "chunk_count": len(chunks),
            "chunks_path": str(output_path),
            "chunking_complete": True
        }
        
    except Exception as e:
        logger.error(f"Chunking failed for {doc_id}: {str(e)}")
        # Return empty result but don't block upload
        return {
            "doc_id": doc_id,
            "document_name": cleaned_json.get("document_name", "unknown"),
            "chunk_count": 0,
            "chunks_path": None,
            "error": str(e),
            "chunking_complete": False
        }

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint to verify RAG service is running.
    
    Returns:
        HealthResponse with status and timestamp
    """
    from datetime import datetime
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        service="rag-researcher-api"
    )


@app.post("/rag/upload", response_model=BatchUploadResponse, tags=["Document Processing"])
async def upload_documents(
    files: List[UploadFile] = File(..., description="Document files to process (PDF, DOCX, TXT, MD)")
):
    """
    Upload and process multiple documents through the multimodal RAG pipeline.
    
    This endpoint:
    - Accepts multiple document uploads (PDF, DOCX, TXT, MD)
    - Processes each file independently
    - Saves extraction to disk (persistent)
    - Returns batch summary with doc_ids and status
    - Returns ONLY summary (not full extraction) - fast response
    
    Args:
        files: List of uploaded document files
        
    Returns:
        BatchUploadResponse with processing summary
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail={"error": "No files provided", "message": "Please upload at least one file"}
        )
    
    batch_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    documents = []
    successful = 0
    failed = 0
    chunks_stored = 0
    
    logger.info(f"Processing batch upload with {len(files)} files, batch_id: {batch_id}, session_id: {session_id}")
    
    for file in files:
        doc_id = str(uuid.uuid4())
        file_status = {
            "doc_id": doc_id,
            "filename": file.filename if file.filename else "unknown",
            "status": "pending"
        }
        
        try:
            # Validate file existence
            if not file or not file.filename:
                raise ValueError("No file provided")
            
            # Sanitize filename
            filename = str(file.filename)
            filename = filename.split(";")[0].strip()
            filename = filename.replace('"', '').replace("'", '')
            
            # Validate file type
            if not validate_file_type(filename, file.content_type):
                raise ValueError(f"Unsupported file type")
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            if not validate_file_size(len(content)):
                raise ValueError(f"File too large")
            
            # Process document
            loader = MultimodalDataLoader()
            file_type = get_file_type_from_filename(filename)
            
            start_time = datetime.now()
            result = loader.process_uploaded_file(content, filename, file_type)
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            if result is None:
                raise ValueError("Document processing failed")
            
            # Save extraction to disk (persistence)
            json_path = save_extraction_to_disk(
                doc_id, 
                result, 
                filename, 
                content, 
                processing_duration
            )
            
            # Run cleaning stage (pipeline step 2)
            try:
                # Load the saved extraction JSON
                extraction_json_path = get_extraction_storage_path() / f"{doc_id}.json"
                with open(extraction_json_path, 'r', encoding='utf-8') as f:
                    extraction_json = json.load(f)
                
                # Run cleaner
                cleaner = RAGTextCleaner()
                cleaned_json = cleaner.clean_extracted_document(extraction_json)
                cleaned_path = cleaner.save_cleaned_document(cleaned_json)
                
                logger.info(f"Cleaning completed: {cleaned_path}")
                file_status["cleaned_path"] = cleaned_path
                
            except Exception as e:
                # Cleaning failure should NOT block upload
                # Log warning but continue
                logger.warning(f"Cleaning stage failed for {doc_id}: {str(e)}")
                logger.warning(f"Continuing with upload (cleaning is non-blocking)")
            
            # Run chunking stage (pipeline step 3) - NON-BLOCKING
            try:
                # Load saved cleaned JSON
                from pathlib import Path as PathLib
                cleaned_json_path = PathLib(cleaned_path)
                with open(cleaned_json_path, 'r', encoding='utf-8') as f:
                    cleaned_json = json.load(f)
                
                # EXTRACT METADATA from cleaned JSON - CRITICAL for audit/traceability
                # Metadata is at top level of cleaned JSON
                document_metadata = {}
                
                # Required metadata fields
                if "filename" in cleaned_json:
                    document_metadata["document_name"] = cleaned_json["filename"]
                else:
                    logger.warning(f"Missing 'filename' in cleaned JSON for {doc_id}")
                    document_metadata["document_name"] = "unknown"
                
                if "doc_id" in cleaned_json:
                    document_metadata["doc_id"] = cleaned_json["doc_id"]
                else:
                    document_metadata["doc_id"] = doc_id
                
                # Metadata from nested "metadata" object
                if "metadata" in cleaned_json:
                    meta = cleaned_json["metadata"]
                    
                    if "source" in meta:
                        document_metadata["source"] = meta["source"]
                    else:
                        logger.warning(f"Missing 'source' in metadata for {doc_id}")
                        document_metadata["source"] = "unknown"
                    
                    if "file_type" in meta:
                        document_metadata["file_type"] = meta["file_type"]
                    
                    if "created_at" in meta:
                        document_metadata["ingestion_timestamp"] = meta["created_at"]
                    else:
                        logger.warning(f"Missing 'created_at' in metadata for {doc_id}")
                        document_metadata["ingestion_timestamp"] = "unknown"
                    
                    if "file_size" in meta:
                        document_metadata["file_size"] = meta["file_size"]
                else:
                    logger.warning(f"Missing 'metadata' object in cleaned JSON for {doc_id}")
                    document_metadata["source"] = "unknown"
                    document_metadata["ingestion_timestamp"] = "unknown"
                
                # Load extraction JSON to get extraction_version
                try:
                    extraction_json_path = get_extraction_storage_path() / f"{doc_id}.json"
                    with open(extraction_json_path, 'r', encoding='utf-8') as f:
                        extraction_json = json.load(f)
                    
                    if "extraction_version" in extraction_json:
                        document_metadata["extraction_version"] = extraction_json["extraction_version"]
                    else:
                        logger.warning(f"Missing 'extraction_version' in extraction JSON for {doc_id}")
                        document_metadata["extraction_version"] = "unknown"
                    
                    if "file_hash" in extraction_json:
                        document_metadata["file_hash"] = extraction_json["file_hash"]
                    
                except Exception as e:
                    logger.warning(f"Could not load extraction JSON for metadata: {str(e)}")
                    document_metadata["extraction_version"] = "unknown"
                
                # Add metadata to cleaned JSON for chunkers to use
                cleaned_json.update(document_metadata)
                
                logger.info(f"Extracted metadata for {doc_id}: {list(document_metadata.keys())}")
                
                # Run ONLY semantic percentile chunking (PRODUCTION DECISION)
                chunking_result = save_chunks_to_disk(doc_id, cleaned_json)
                
                # Log chunking results
                chunk_count = chunking_result["chunk_count"]
                logger.info(f"Chunking completed: {chunk_count} chunks (semantic percentile)")
                
                # Build chunking status (summary only, no chunk text)
                file_status["chunking"] = {
                    "doc_id": chunking_result["doc_id"],
                    "document_name": chunking_result["document_name"],
                    "chunk_count": chunking_result["chunk_count"],
                    "chunks_path": chunking_result["chunks_path"]
                }
                
                if "error" in chunking_result:
                    file_status["chunking"]["error"] = chunking_result["error"]
                
                # Build BM25 sparse index for document (HYBRID RETRIEVAL ENHANCEMENT)
                try:
                    # Load chunks from disk for BM25 indexing
                    chunks_file_path = Path(chunking_result["chunks_path"])
                    if chunks_file_path.exists():
                        with open(chunks_file_path, 'r', encoding='utf-8') as f:
                            chunks_data = json.load(f)
                        
                        # Extract chunks list from chunks_data
                        chunks_list = chunks_data.get("chunks", [])
                        
                        # Build BM25 index using SparseIndexService singleton
                        sparse_index_service = SparseIndexService()
                        sparse_index_service.build_index(doc_id, chunks_list)
                        
                        logger.info(f"BM25 sparse index built for doc_id={doc_id}")
                    else:
                        logger.warning(f"Chunks file not found for BM25 indexing: {chunks_file_path}")
                except Exception as e:
                    # Sparse index building should NOT block upload
                    # Log warning but continue
                    logger.warning(f"BM25 index building failed for {doc_id}: {str(e)}")
                    logger.warning(f"Continuing with upload (BM25 index is non-blocking)")
                
                # Run embedding stage (pipeline step 4) - BLOCKING (fails upload if error)
                try:
                    logger.info(f"Starting embedding for {doc_id}")
                    
                    # Initialize embedder
                    embedder = DocumentEmbedder(batch_size=64)
                    
                    # Embed document
                    embedding_result = embedder.embed_document(doc_id)
                    
                    # Log embedding results
                    embedding_count = embedding_result["embedding_count"]
                    logger.info(f"Embedding completed: {embedding_count} embeddings (text-embedding-3-large)")
                    
                    # Build embedding status (summary only, no vector data)
                    file_status["embedding"] = {
                        "doc_id": embedding_result["doc_id"],
                        "document_name": embedding_result["document_name"],
                        "embedding_count": embedding_result["embedding_count"],
                        "embedding_path": embedding_result["embedding_path"],
                        "embedding_model": embedding_result["embedding_model"],
                        "embedding_dim": embedding_result["embedding_dim"]
                    }
                    
                    # Run vector store stage (pipeline step 5) - BLOCKING (fails upload if error)
                    try:
                        logger.info(f"Starting vector store upsert for {doc_id}")
                        
                        # Load embeddings from disk
                        embeddings_path = Path(embedding_result["embedding_path"])
                        with open(embeddings_path, 'r', encoding='utf-8') as f:
                            embeddings_data = json.load(f)
                        
                        embeddings = embeddings_data.get("embeddings", [])
                        logger.info(f"Loaded {len(embeddings)} embeddings for upsert")
                        
                        # Initialize vector store
                        vector_store = VectorStore(
                            url="http://localhost:6333",
                            collection_name="rag_chunks",
                            vector_size=3072
                        )
                        
                        # Upsert embeddings to Qdrant with session_id
                        upsert_result = vector_store.upsert_document(
                            doc_id=doc_id,
                            embeddings_data=embeddings,
                            batch_size=200,
                            session_id=session_id
                        )
                        
                        # Log upsert results
                        points_upserted = upsert_result["points_upserted"]
                        logger.info(f"Vector store upsert completed: {points_upserted} points")
                        
                        # Build vector store status (summary only)
                        chunks_stored += upsert_result["points_upserted"]
                        file_status["vector_store"] = {
                            "doc_id": upsert_result["doc_id"],
                            "points_upserted": upsert_result["points_upserted"],
                            "batches": upsert_result["batches"],
                            "session_id": session_id
                        }
                        
                    except VectorStoreError as e:
                        # Vector store failure BLOCKS upload (hard fail)
                        logger.error(f"Vector store stage failed for {doc_id}: {str(e)}")
                        logger.error(f"Upload failed: vector store is blocking")
                        raise HTTPException(
                            status_code=500,
                            detail={
                                "error": "Vector store failed",
                                "message": str(e),
                                "doc_id": doc_id
                            }
                        )
                    
                except EmbeddingError as e:
                    # Embedding failure BLOCKS upload (hard fail)
                    logger.error(f"Embedding stage failed for {doc_id}: {str(e)}")
                    logger.error(f"Upload failed: embedding is blocking")
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": "Embedding failed",
                            "message": str(e),
                            "doc_id": doc_id
                        }
                    )
                
            except Exception as e:
                # Chunking failure should NOT block upload
                # Log warning but continue
                logger.error(f"Chunking stage failed for {doc_id}: {str(e)}")
                logger.error(f"Continuing with upload (chunking is non-blocking)")
                
                # SAFETY: Try to preserve any chunks that were saved before error
                chunking_status = {
                    "error": str(e),
                    "doc_id": doc_id,
                    "document_name": cleaned_json.get("document_name", "unknown"),
                    "chunk_count": 0,
                    "chunks_path": None
                }
                
                try:
                    # Try to load existing chunks
                    chunks_path = get_chunking_storage_path() / f"{doc_id}_chunks.json"
                    if chunks_path.exists():
                        with open(chunks_path, 'r', encoding='utf-8') as f:
                            chunks_data = json.load(f)
                            # chunks_data is a dict with "chunks" key
                            chunking_status["chunk_count"] = len(chunks_data["chunks"])
                            chunking_status["chunks_path"] = str(chunks_path)
                except Exception as e2:
                    logger.warning(f"Could not preserve chunking results: {str(e2)}")
                
                file_status["chunking"] = chunking_status
            
            file_status["status"] = "processed"
            file_status["json_path"] = json_path
            successful += 1
            
            logger.info(f"Successfully processed {filename} -> {doc_id}")
            
        except Exception as e:
            # Safe processing: log error but continue with next file
            file_status["status"] = "failed"
            file_status["error"] = str(e)
            failed += 1
            logger.error(f"Error processing file {file.filename if file.filename else 'unknown'}: {str(e)}")
        
        documents.append(file_status)
    
    logger.info(f"Batch upload complete: {successful}/{len(files)} successful, {chunks_stored} chunks stored")
    
    return BatchUploadResponse(
        batch_id=batch_id,
        session_id=session_id,
        documents=documents,
        total_files=len(files),
        successful=successful,
        failed=failed
    )


@app.post("/rag/query", response_model=RAGQueryResponse, tags=["RAG Query"])
async def rag_query(request: RAGQueryRequest):
    """
    Query RAG system to get an answer for a question.
    
    This endpoint:
    - Automatically decomposes complex queries (LLM-based)
    - Retrieves relevant chunks from Qdrant (filtered by session_id)
    - Reranks chunks using cross-encoder
    - Generates answer using LLM with retrieved context
    - Returns structured response with answer, evidence, limitations, citations
    
    Backward Compatible:
    - Single queries: Same performance as before
    - Multi-query scenarios: Enhanced with decomposition and distinct answers
    
    Args:
        request: RAGQueryRequest with query and session_id
        
    Returns:
        RAGQueryResponse with answer and metadata
    """
    logger.info(f"RAG query for session_id={request.session_id}, query: '{request.query}'")
    
    try:
        # Initialize retriever
        retriever = Retriever(dense_top_k=40, rerank_top_n=6)
        
        # Initialize generator with retriever (required for generate_smart)
        generator = LLMGenerator(retriever=retriever)
        
        # Step 1: Smart generation with automatic decomposition
        result = generator.generate_smart(
            query=request.query,
            session_id=request.session_id,
            enable_decomposition=True  # Enable LLM-based decomposition
        )
        
        logger.info(f"Answer generated successfully")
        
        # Step 2: Build response
        return RAGQueryResponse(
            success=result.get("success", True),
            query=request.query,
            session_id=request.session_id,
            answer=result.get("answer", ""),
            evidence=result.get("evidence", ""),
            limitations=result.get("limitations", ""),
            citations=result.get("citations", []),
            chunks_used=result.get("chunks_count", 0),
            confidence=result.get("confidence", "low"),
            model=result.get("model", "N/A"),
            timestamp=datetime.now().isoformat(),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}", exc_info=True)
        return RAGQueryResponse(
            success=False,
            query=request.query,
            session_id=request.session_id,
            answer="An error occurred while processing your query.",
            evidence="",
            limitations=str(e),
            citations=[],
            chunks_used=0,
            confidence="low",
            model="N/A",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting RAG Researcher FastAPI Service")
    logger.info(f"OpenRouter API: {Config.OPENROUTER_BASE_URL}")
    logger.info(f"Storage path: {Config.get_storage_path()}")
    logger.info(f"Extraction path: {get_extraction_storage_path()}")
    
    # Run the FastAPI server
    # Access API docs at: http://localhost:8000/docs
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )