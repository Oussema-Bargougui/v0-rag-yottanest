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