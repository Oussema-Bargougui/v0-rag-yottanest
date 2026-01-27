"""
Embedding Layer - Production Implementation

Converts text chunks into vector embeddings using OpenRouter API.
Deterministic caching, strict error handling, JSON-only storage.

Author: Yottanest Team
Version: 1.0.0
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

import httpx

from config import Config


logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Embedding-specific error."""
    pass


class EmbeddingCache:
    """
    Deterministic caching for embeddings.
    
    Cache key: sha256(text + model_name)
    Storage: storage/embedding_cache/<hash>.npy
    """
    
    def __init__(self, cache_dir: Path = None):
        """
        Initialize embedding cache.
        
        Args:
            cache_dir: Cache directory path (defaults to storage/embedding_cache/)
        """
        if cache_dir is None:
            cache_dir = Config.get_storage_path() / "embedding_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Embedding cache initialized: {self.cache_dir}")
    
    def _get_cache_key(self, text: str, model_name: str) -> str:
        """
        Generate cache key from text and model name.
        
        Args:
            text: Text content
            model_name: Model name (e.g., "openai/text-embedding-3-large")
            
        Returns:
            SHA-256 hash as hex string
        """
        key = f"{text}{model_name}"
        return hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    def get(self, text: str, model_name: str) -> np.ndarray:
        """
        Retrieve cached embedding.
        
        Args:
            text: Text content
            model_name: Model name
            
        Returns:
            Embedding vector as numpy array
            
        Raises:
            FileNotFoundError: If cache miss
        """
        cache_key = self._get_cache_key(text, model_name)
        cache_path = self.cache_dir / f"{cache_key}.npy"
        
        if not cache_path.exists():
            raise FileNotFoundError(f"Cache miss: {cache_key}")
        
        vector = np.load(cache_path)
        logger.debug(f"Cache hit: {cache_key}")
        return vector
    
    def set(self, text: str, model_name: str, vector: np.ndarray) -> None:
        """
        Cache embedding vector.
        
        Args:
            text: Text content
            model_name: Model name
            vector: Embedding vector to cache
        """
        cache_key = self._get_cache_key(text, model_name)
        cache_path = self.cache_dir / f"{cache_key}.npy"
        
        np.save(cache_path, vector)
        logger.debug(f"Cache saved: {cache_key}")


class EmbeddingClient:
    """
    OpenRouter API client for embeddings.
    
    Model: openai/text-embedding-3-large
    Dimensions: 3072
    """
    
    def __init__(self):
        """Initialize OpenRouter embedding client."""
        self.api_key = Config.OPENROUTER_API_KEY
        self.base_url = Config.OPENROUTER_BASE_URL
        self.model = "openai/text-embedding-3-large"
        self.expected_dim = 3072
        
        if not self.api_key:
            raise EmbeddingError("OPENROUTER_API_KEY not configured")
        
        logger.info(f"Embedding client initialized: {self.model} (dim={self.expected_dim})")
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Embed a batch of texts.
        
        Args:
            texts: List of text strings (max 64 per batch)
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: On API failure
        """
        if len(texts) > 64:
            raise EmbeddingError(f"Batch size exceeds 64: {len(texts)}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yottanest.com",
            "X-Title": "Yottanest RAG"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        start_time = time.time()
        
        try:
            response = httpx.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "data" not in data:
                raise EmbeddingError(f"Invalid API response: {data}")
            
            embeddings = []
            for item in data["data"]:
                vector = np.array(item["embedding"], dtype=np.float32)
                
                # Validate dimension
                if len(vector) != self.expected_dim:
                    raise EmbeddingError(
                        f"Invalid dimension: {len(vector)} (expected {self.expected_dim})"
                    )
                
                embeddings.append(vector)
            
            latency = time.time() - start_time
            logger.info(f"Batch embedded: {len(texts)} texts in {latency:.2f}s")
            
            return embeddings
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e.response.status_code} - {e.response.text}")
            raise EmbeddingError(f"API request failed: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            raise EmbeddingError(f"Embedding failed: {str(e)}")


class DocumentEmbedder:
    """
    Production-ready document embedder.
    
    Workflow:
    1. Load chunks from storage
    2. Embed chunk.text ONLY (not metadata)
    3. Cache results deterministically
    4. Attach metadata as payload
    5. Save to storage/embeddings/<doc_id>.json
    """
    
    def __init__(self, batch_size: int = 64):
        """
        Initialize document embedder.
        
        Args:
            batch_size: Batch size for API calls (default 64)
        """
        self.batch_size = batch_size
        self.client = EmbeddingClient()
        self.cache = EmbeddingCache()
        self.storage_dir = Config.get_storage_path() / "embeddings"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Document embedder initialized (batch_size={batch_size})")
    
    def _build_payload(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build metadata payload for chunk.
        
        Args:
            chunk: Chunk dictionary with metadata
            
        Returns:
            Payload dictionary (excluding text and vector)
        """
        # Copy all fields except 'text' (we embed only text)
        payload = {k: v for k, v in chunk.items() if k != "text"}
        
        # Ensure required fields exist
        required_fields = [
            "doc_id", "document_name", "chunk_index", "chunk_size",
            "page_numbers", "char_range", "strategy"
        ]
        
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Missing required field in payload: {field}")
                payload[field] = None
        
        return payload
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embed a list of chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of embedded chunks with structure:
            {
                "id": "chunk_id",
                "vector": [float x 3072],
                "payload": { metadata }
            }
        """
        if not chunks:
            logger.warning("No chunks to embed")
            return []
        
        logger.info(f"Starting embedding for {len(chunks)} chunks")
        start_time = time.time()
        
        embedded_chunks = []
        cache_hits = 0
        cache_misses = 0
        
        # Process in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_start = time.time()
            
            logger.info(f"Processing batch {i//self.batch_size + 1}: {len(batch)} chunks")
            
            batch_embeddings = []
            
            # Embed each text in batch
            for chunk in batch:
                text = chunk.get("text", "")
                model_name = self.client.model
                
                # Check cache
                try:
                    vector = self.cache.get(text, model_name)
                    cache_hits += 1
                    batch_embeddings.append(vector)
                except FileNotFoundError:
                    cache_misses += 1
                    batch_embeddings.append(None)  # Placeholder for miss
            
            # Call API only for cache misses
            miss_indices = [j for j, v in enumerate(batch_embeddings) if v is None]
            
            if miss_indices:
                miss_texts = [batch[j]["text"] for j in miss_indices]
                
                try:
                    miss_embeddings = self.client.embed_batch(miss_texts)
                    
                    # Update batch with new embeddings
                    for idx, embedding in zip(miss_indices, miss_embeddings):
                        batch_embeddings[idx] = embedding
                        
                        # Cache result
                        text = batch[idx]["text"]
                        model_name = self.client.model
                        self.cache.set(text, model_name, embedding)
                        
                except EmbeddingError as e:
                    # Hard fail - no partial success
                    logger.error(f"Batch embedding failed: {str(e)}")
                    raise EmbeddingError(f"Embedding failed: {str(e)}")
            
            # Build embedded chunks
            for j, (chunk, vector) in enumerate(zip(batch, batch_embeddings)):
                # CRITICAL: Preserve text for vector_store (needed for retrieval)
                embedded_chunk = {
                    "id": chunk.get("chunk_id", f"chunk_{i+j}"),
                    "vector": vector.tolist(),  # Convert numpy to list for JSON
                    "text": chunk.get("text", ""),  # Preserve text for vector_store
                    "payload": self._build_payload(chunk)
                }
                embedded_chunks.append(embedded_chunk)
            
            batch_latency = time.time() - batch_start
            logger.info(f"Batch complete: {len(batch)} chunks in {batch_latency:.2f}s")
        
        # Final validation
        total_time = time.time() - start_time
        avg_time_per_chunk = total_time / len(chunks)
        
        logger.info(f"Embedding complete:")
        logger.info(f"  Total chunks: {len(chunks)}")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Avg time per chunk: {avg_time_per_chunk:.3f}s")
        logger.info(f"  Cache hits: {cache_hits}")
        logger.info(f"  Cache misses: {cache_misses}")
        logger.info(f"  Cache hit rate: {cache_hits/(cache_hits+cache_misses)*100:.1f}%")
        
        # Validate all embeddings have correct dimension
        for ec in embedded_chunks:
            if len(ec["vector"]) != self.client.expected_dim:
                raise EmbeddingError(
                    f"Invalid dimension: {len(ec['vector'])} "
                    f"(expected {self.client.expected_dim})"
                )
        
        logger.info(f"Validated all embeddings: {self.client.expected_dim} dimensions")
        
        return embedded_chunks
    
    def embed_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Load chunks, embed, and save to disk.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary with embedding summary
        """
        # Load chunks
        chunks_path = Config.get_storage_path() / "chunks" / f"{doc_id}_chunks.json"
        
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        chunks = chunks_data.get("chunks", [])
        logger.info(f"Loaded {len(chunks)} chunks from {chunks_path}")
        
        # Embed chunks
        embedded_chunks = self.embed_chunks(chunks)
        
        # Save embeddings
        output_path = self.storage_dir / f"{doc_id}.json"
        
        result = {
            "doc_id": doc_id,
            "document_name": chunks_data.get("document_name", "unknown"),
            "chunk_strategy": chunks_data.get("chunk_strategy", "unknown"),
            "embedding_model": self.client.model,
            "embedding_dim": self.client.expected_dim,
            "total_embeddings": len(embedded_chunks),
            "embeddings": embedded_chunks
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved embeddings: {output_path}")
        
        return {
            "doc_id": doc_id,
            "document_name": chunks_data.get("document_name", "unknown"),
            "embedding_count": len(embedded_chunks),
            "embedding_path": str(output_path),
            "embedding_model": self.client.model,
            "embedding_dim": self.client.expected_dim
        }