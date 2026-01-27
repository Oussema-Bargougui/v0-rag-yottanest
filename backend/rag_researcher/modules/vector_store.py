"""
Vector Store - Production Implementation

Stores embeddings with metadata in Qdrant vector database.
Storage-only layer (no retrieval logic).

Author: Yottanest Team
Version: 1.0.0
"""

import json
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    CollectionInfo
)

from config import Config


logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Vector store-specific error."""
    pass


class VectorStore:
    """
    Production-ready Qdrant vector store.
    
    Stores embeddings with metadata for future retrieval.
    Storage-only (no query/retrieval logic).
    """
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "rag_chunks",
        vector_size: int = 3072
    ):
        """
        Initialize Qdrant vector store.
        
        Args:
            url: Qdrant server URL
            collection_name: Collection name
            vector_size: Embedding dimension (must be 3072)
        """
        self.url = url
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize Qdrant client
        try:
            self.client = QdrantClient(url=url, timeout=60.0)
            logger.info(f"Connected to Qdrant: {url}")
        except Exception as e:
            raise VectorStoreError(f"Failed to connect to Qdrant: {str(e)}")
        
        # Auto-create collection if missing
        self._ensure_collection_exists()
        
        logger.info(f"Vector store initialized: {collection_name} (dim={vector_size})")
    
    def _ensure_collection_exists(self) -> None:
        """
        Create collection if it doesn't exist.
        
        Collection configuration:
        - Vectors: 3072 dimensions, Cosine distance
        - Payload: JSON metadata (flat structure)
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                
                logger.info(f"Collection created successfully: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
                
        except Exception as e:
            raise VectorStoreError(f"Failed to ensure collection exists: {str(e)}")
    
    def _validate_embedding(self, vector: List[float]) -> None:
        """
        Validate embedding vector.
        
        Args:
            vector: Embedding vector
            
        Raises:
            VectorStoreError: If validation fails
        """
        if not isinstance(vector, list):
            raise VectorStoreError(f"Vector must be a list, got {type(vector)}")
        
        if len(vector) != self.vector_size:
            raise VectorStoreError(
                f"Invalid vector dimension: {len(vector)} "
                f"(expected {self.vector_size})"
            )
        
        if any(not isinstance(x, (int, float)) for x in vector):
            raise VectorStoreError("Vector contains non-numeric values")
    
    def _validate_point_id(self, point_id: str) -> None:
        """
        Validate point ID.
        
        Args:
            point_id: Point ID (should be chunk_id)
            
        Raises:
            VectorStoreError: If validation fails
        """
        if not point_id:
            raise VectorStoreError("Point ID cannot be empty")
        
        if not isinstance(point_id, str):
            raise VectorStoreError(f"Point ID must be string, got {type(point_id)}")
    
    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        """
        Validate payload metadata.
        
        Args:
            payload: Payload dictionary
            
        Raises:
            VectorStoreError: If validation fails
        """
        required_fields = ["doc_id", "chunk_id", "chunk_index"]
        
        for field in required_fields:
            if field not in payload:
                raise VectorStoreError(f"Missing required field in payload: {field}")
        
        # Ensure JSON-serializable
        try:
            json.dumps(payload)
        except TypeError as e:
            raise VectorStoreError(f"Payload is not JSON-serializable: {str(e)}")
    
    def _build_payload(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build flat payload from chunk metadata including text.
        
        Args:
            chunk_data: Chunk dictionary with payload
            
        Returns:
            Flat payload dictionary (includes text field)
        """
        payload = chunk_data.get("payload", {})
        
        # CRITICAL: Include text in payload for retriever
        if "text" in chunk_data:
            payload["text"] = chunk_data["text"]
        
        # Ensure required fields are present
        if "chunk_id" not in payload:
            payload["chunk_id"] = chunk_data.get("id", "")
        
        # Flatten char_range to individual fields
        if "char_range" in payload and isinstance(payload["char_range"], list):
            payload["char_start"] = payload["char_range"][0]
            payload["char_end"] = payload["char_range"][1]
            del payload["char_range"]
        
        return payload
    
    def upsert_document(
        self,
        doc_id: str,
        embeddings_data: List[Dict[str, Any]],
        batch_size: int = 200,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Upsert document embeddings to Qdrant with chunk text in payload.
        
        Args:
            doc_id: Document ID
            embeddings_data: List of embedding records from embedder
            batch_size: Batch size for upsert (default 200)
            session_id: Session ID for session isolation (optional)
            
        Returns:
            Dictionary with upsert summary
            
        Raises:
            VectorStoreError: On validation or upsert failure
        """
        if not embeddings_data:
            logger.warning(f"No embeddings to upsert for {doc_id}")
            return {
                "doc_id": doc_id,
                "points_upserted": 0,
                "batches": 0
            }
        
        logger.info(f"Starting upsert for {doc_id}: {len(embeddings_data)} points (session_id={session_id})")
        
        total_upserted = 0
        batch_count = 0
        
        # Process in batches
        for i in range(0, len(embeddings_data), batch_size):
            batch = embeddings_data[i:i + batch_size]
            batch_count += 1
            
            logger.info(f"Upserting batch {batch_count}: {len(batch)} points")
            
            points = []
            
            for emb_data in batch:
                try:
                    # Extract data
                    vector = emb_data.get("vector", [])
                    point_id = emb_data.get("id", "")
                    
                    # CRITICAL: Build payload including text from embedder output
                    # Use _build_payload which preserves text
                    payload = self._build_payload(emb_data)
                    
                    # Add session_id to payload if provided
                    if session_id:
                        payload["session_id"] = session_id
                    
                    # CRITICAL: Verify text is in payload (should be from emb_data["text"])
                    if "text" not in payload or not payload["text"]:
                        raise VectorStoreError(
                            f"Chunk text not found in payload for chunk_id={point_id}. "
                            f"emb_data has 'text': {'text' in emb_data}, "
                            f"payload has 'text': {'text' in payload}"
                        )
                    
                    # Validate
                    self._validate_embedding(vector)
                    self._validate_point_id(point_id)
                    self._validate_payload(payload)
                    
                    # Create point
                    point = PointStruct(
                        id=point_id,  # Use chunk_id as point ID (NOT random)
                        vector=vector,
                        payload=payload
                    )
                    
                    points.append(point)
                    
                except (VectorStoreError, Exception) as e:
                    # Validation error - fail hard (no silent failures)
                    logger.error(f"Validation failed for point in batch {batch_count}: {str(e)}")
                    raise VectorStoreError(f"Validation failed: {str(e)}")
            
            # Upsert batch
            try:
                operation_info = self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                logger.info(f"Batch {batch_count} upserted: {len(points)} points")
                total_upserted += len(points)
                
            except Exception as e:
                logger.error(f"Upsert failed for batch {batch_count}: {str(e)}")
                raise VectorStoreError(f"Upsert failed: {str(e)}")
        
        # Log summary
        logger.info(f"Upsert complete for {doc_id}:")
        logger.info(f"  Total points upserted: {total_upserted}")
        logger.info(f"  Total batches: {batch_count}")
        
        return {
            "doc_id": doc_id,
            "points_upserted": total_upserted,
            "batches": batch_count
        }
    
    def get_collection_info(self) -> CollectionInfo:
        """
        Get collection information.
        
        Returns:
            CollectionInfo object with collection details
        """
        try:
            return self.client.get_collection(self.collection_name)
        except Exception as e:
            raise VectorStoreError(f"Failed to get collection info: {str(e)}")
    
    def count_points(self) -> int:
        """
        Count total points in collection.
        
        Returns:
            Number of points in collection
        """
        try:
            result = self.client.count(self.collection_name)
            return result.count
        except Exception as e:
            raise VectorStoreError(f"Failed to count points: {str(e)}")