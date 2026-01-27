"""
Retriever Layer - Hybrid Retrieval Implementation

Three-stage retrieval pipeline:
1. Dense retrieval (Qdrant) - high recall
2. Sparse retrieval (BM25) - high precision for keywords
3. Hybrid merge + deduplication - combine results
4. Cross-encoder reranking (BGE) - high precision

Author: Yottanest Team
Version: 2.0.0 - Hybrid Retrieval with Sparse Index Service
"""

import logging
import time
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter
import httpx
import numpy as np
from pathlib import Path
import sys
import json

# Fix import when running module directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from .sparse_index_service import SparseIndexService


logger = logging.getLogger(__name__)


class RetrieverError(Exception):
    """Retriever-specific error."""
    pass


class DenseRetriever:
    """
    Dense vector retriever using Qdrant.
    
    Responsibilities:
    - Connect to Qdrant
    - Embed query using same model as documents
    - Perform vector search (cosine similarity)
    - Return raw candidates with text from payload
    - Filter by session_id for session isolation
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "rag_chunks",
        embedding_model: str = "openai/text-embedding-3-large",
        top_k: int = 40
    ):
        """
        Initialize dense retriever.
        
        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name in Qdrant
            embedding_model: OpenRouter embedding model
            top_k: Number of candidates to retrieve
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.top_k = top_k
        
        # Initialize Qdrant client
        try:
            self.client = QdrantClient(url=qdrant_url, timeout=60.0)
            logger.info(f"Dense retriever connected: {qdrant_url}")
        except Exception as e:
            raise RetrieverError(f"Failed to connect to Qdrant: {str(e)}")
        
        # Initialize embedding client (reuse from embedder module)
        self.api_key = Config.OPENROUTER_API_KEY
        self.base_url = Config.OPENROUTER_BASE_URL
        
        if not self.api_key:
            raise RetrieverError("OPENROUTER_API_KEY not configured")
    
    def _embed_query(self, query: str) -> List[float]:
        """
        Embed query using OpenRouter API.
        
        Args:
            query: User query string
            
        Returns:
            Query embedding vector (3072 dimensions)
            
        Raises:
            RetrieverError: On API failure
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yottanest.com",
            "X-Title": "Yottanest RAG"
        }
        
        payload = {
            "model": self.embedding_model,
            "input": [query]
        }
        
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
                raise RetrieverError(f"Invalid API response: {data}")
            
            embedding = data["data"][0]["embedding"]
            
            # Validate dimension
            if len(embedding) != 3072:
                raise RetrieverError(
                    f"Invalid embedding dimension: {len(embedding)} (expected 3072)"
                )
            
            return embedding
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e.response.status_code} - {e.response.text}")
            raise RetrieverError(f"Embedding API failed: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Query embedding failed: {str(e)}")
            raise RetrieverError(f"Query embedding failed: {str(e)}")
    
    def retrieve(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-K candidate chunks from Qdrant.
        
        Args:
            query: User query string
            session_id: Optional session_id for session isolation
            
        Returns:
            List of candidate chunks with text from payload:
            {
                "chunk_id": str,
                "text": str,
                "doc_id": str,
                "document_name": str,
                "page_numbers": list,
                "char_start": int,
                "char_end": int,
                "score": float,
                "retrieval_type": "dense"
            }
        """
        logger.info(f"Dense retrieval for query: '{query}' (session_id={session_id})")
        start_time = time.time()
        
        # Embed query
        query_vector = self._embed_query(query)
        logger.debug(f"Query embedded (dim={len(query_vector)})")
        
        # Search Qdrant using scroll and manual scoring
        try:
            # Scroll all points and score them manually
            # This is slower but works with all Qdrant versions
            all_points = []
            offset = None
            limit = 1000
            
            while True:
                records, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=limit,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                all_points.extend(records)
                
                if not next_offset or len(records) == 0:
                    break
                    
                offset = next_offset
            
            # Filter by session_id if provided
            if session_id:
                all_points = [
                    record for record in all_points
                    if record.payload and record.payload.get("session_id") == session_id
                ]
                logger.debug(f"Filtered to {len(all_points)} points by session_id={session_id}")
            
            # Calculate cosine similarity for each point
            scored_points = []
            for record in all_points:
                if record.vector is not None:
                    # Convert to numpy arrays
                    query_arr = np.array(query_vector)
                    chunk_arr = np.array(record.vector)
                    
                    # Cosine similarity
                    dot_product = np.dot(query_arr, chunk_arr)
                    norm_query = np.linalg.norm(query_arr)
                    norm_chunk = np.linalg.norm(chunk_arr)
                    
                    if norm_query == 0 or norm_chunk == 0:
                        similarity = 0.0
                    else:
                        similarity = dot_product / (norm_query * norm_chunk)
                    
                    scored_points.append({
                        'id': record.id,
                        'score': float(similarity),
                        'payload': record.payload
                    })
            
            # Sort by similarity (descending) and take top_k
            scored_points.sort(key=lambda x: x['score'], reverse=True)
            search_results = scored_points[:self.top_k]
            
        except Exception as e:
            logger.error(f"Qdrant search failed: {str(e)}")
            raise RetrieverError(f"Qdrant search failed: {str(e)}")
        
        # Build candidate list with required fields from payload
        candidates = []
        for result in search_results:
            payload = result.get('payload', {})
            chunk_id = result.get('id', '')
            score = result.get('score', 0.0)
            
            # Extract text from payload (CRITICAL - already stored in Qdrant)
            if "text" not in payload:
                raise ValueError(
                    f"Qdrant payload missing chunk text for chunk_id={chunk_id}"
                )
            
            chunk_text = payload.get("text", "")
            
            # Build candidate with required output format
            candidate = {
                "chunk_id": str(chunk_id),
                "text": chunk_text,
                "doc_id": payload.get("doc_id", ""),
                "document_name": payload.get("document_name", ""),
                "page_numbers": payload.get("page_numbers", []),
                "char_start": payload.get("char_start", 0),
                "char_end": payload.get("char_end", 0),
                "score": score,
                "retrieval_type": "dense"
            }
            candidates.append(candidate)
        
        latency = time.time() - start_time
        logger.info(f"Dense retrieval: {len(candidates)} candidates in {latency:.3f}s")
        
        return candidates


class HybridRetriever:
    """
    Hybrid retriever combining dense and sparse results.
    
    Responsibilities:
    - Merge dense and sparse candidates
    - Deduplicate by chunk_id
    - Combine scores using weighted combination
    - Limit to max candidates
    """
    
    def __init__(self, max_candidates: int = 60, dense_weight: float = 0.6, sparse_weight: float = 0.4):
        """
        Initialize hybrid retriever.
        
        Args:
            max_candidates: Maximum candidates after merge
            dense_weight: Weight for dense scores (0-1)
            sparse_weight: Weight for sparse scores (0-1)
        """
        self.max_candidates = max_candidates
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        logger.info(f"Hybrid retriever initialized: max_candidates={max_candidates}, dense_w={dense_weight}, sparse_w={sparse_weight}")
    
    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            results: List of candidates with "score" field
            
        Returns:
            Results with normalized "normalized_score" field
        """
        if not results:
            return []
        
        scores = [r["score"] for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            for r in results:
                r["normalized_score"] = 0.5
        else:
            for r in results:
                r["normalized_score"] = (r["score"] - min_score) / (max_score - min_score)
        
        return results
    
    def merge(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge dense and sparse results with weighted score combination.
        
        Args:
            dense_results: Candidates from dense retriever
            sparse_results: Candidates from sparse retriever
            
        Returns:
            Merged and deduplicated candidates (max configured)
        """
        logger.info(f"Merging: dense={len(dense_results)}, sparse={len(sparse_results)}")
        start_time = time.time()
        
        # Normalize scores separately
        dense_normalized = self._normalize_scores(dense_results)
        sparse_normalized = self._normalize_scores(sparse_results)
        
        # Create mapping: chunk_id -> best candidate
        merged_map: Dict[str, Dict[str, Any]] = {}
        
        # Add dense results (with normalized scores)
        for candidate in dense_normalized:
            chunk_id = candidate["chunk_id"]
            weighted_score = self.dense_weight * candidate["normalized_score"]
            
            if chunk_id not in merged_map:
                merged_map[chunk_id] = candidate.copy()
                merged_map[chunk_id]["retrieval_type"] = "dense"
                merged_map[chunk_id]["weighted_score"] = weighted_score
            else:
                # Keep higher weighted score
                if weighted_score > merged_map[chunk_id]["weighted_score"]:
                    merged_map[chunk_id] = candidate.copy()
                    merged_map[chunk_id]["retrieval_type"] = "dense"
                    merged_map[chunk_id]["weighted_score"] = weighted_score
        
        # Add sparse results (with normalized scores)
        for candidate in sparse_normalized:
            chunk_id = candidate["chunk_id"]
            weighted_score = self.sparse_weight * candidate["normalized_score"]
            
            if chunk_id not in merged_map:
                merged_map[chunk_id] = candidate.copy()
                merged_map[chunk_id]["retrieval_type"] = "sparse"
                merged_map[chunk_id]["weighted_score"] = weighted_score
            else:
                # Keep higher weighted score
                if weighted_score > merged_map[chunk_id]["weighted_score"]:
                    merged_map[chunk_id] = candidate.copy()
                    merged_map[chunk_id]["retrieval_type"] = "sparse"
                    merged_map[chunk_id]["weighted_score"] = weighted_score
                elif merged_map[chunk_id]["retrieval_type"] == "dense":
                    # Both found, mark as hybrid
                    merged_map[chunk_id]["retrieval_type"] = "hybrid"
        
        # Convert to list
        merged = list(merged_map.values())
        
        # Sort by weighted score (descending)
        merged.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # Limit to max_candidates
        merged = merged[:self.max_candidates]
        
        # Update retrieval types for dual matches
        for candidate in merged:
            chunk_id = candidate["chunk_id"]
            dense_found = any(r["chunk_id"] == chunk_id for r in dense_results)
            sparse_found = any(r["chunk_id"] == chunk_id for r in sparse_results)
            
            if dense_found and sparse_found:
                candidate["retrieval_type"] = "hybrid"
        
        latency = time.time() - start_time
        logger.info(f"Merge complete: {len(merged)} candidates in {latency:.3f}s")
        
        # Log breakdown
        dense_only = sum(1 for r in merged if r["retrieval_type"] == "dense")
        sparse_only = sum(1 for r in merged if r["retrieval_type"] == "sparse")
        hybrid = sum(1 for r in merged if r["retrieval_type"] == "hybrid")
        logger.info(f"  Dense-only: {dense_only}, Sparse-only: {sparse_only}, Hybrid: {hybrid}")
        
        return merged


class CrossEncoderReranker:
    """
    Cross-encoder reranker using BGE model.
    
    Responsibilities:
    - Load BGE reranker model
    - Score (query, chunk_text) pairs
    - Sort and filter candidates
    - Return top-N reranked chunks
    """
    
    def __init__(
        self,
        model_name: str = None,
        top_n: int = None,
        batch_size: int = 16
    ):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model name (uses Config.RERANKER_MODEL if None)
            top_n: Number of top chunks to return (uses Config.RETRIEVER_CONFIG if None)
            batch_size: Batch size for scoring
        """
        # Use config defaults if not specified
        if model_name is None:
            model_name = Config.RERANKER_MODEL
        if top_n is None:
            top_n = Config.RETRIEVER_CONFIG.get("rerank_top_n", 6)
        
        self.model_name = model_name
        self.top_n = top_n
        self.batch_size = batch_size
        
        # Load model
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading cross-encoder model: {model_name}")
            self.model = CrossEncoder(model_name)
            logger.info(f"Model loaded successfully: {model_name}")
        except ImportError:
            raise RetrieverError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise RetrieverError(f"Failed to load model: {str(e)}")
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder.
        
        Args:
            query: User query string
            candidates: List of candidates from hybrid retriever (must have "text" field)
            
        Returns:
            Reranked and sorted candidates (top-N) with rerank_score
        """
        if not candidates:
            logger.warning("No candidates to rerank")
            return []
        
        logger.info(f"Cross-encoder reranking: {len(candidates)} candidates")
        start_time = time.time()
        
        # Extract chunk texts from candidates (already in payload)
        chunk_texts = []
        for candidate in candidates:
            text = candidate.get("text", "")
            if not text:
                logger.warning(f"Empty text for chunk_id={candidate.get('chunk_id')}")
                continue
            chunk_texts.append(text)
        
        # Create (query, chunk_text) pairs
        pairs = [(query, text) for text in chunk_texts if text]
        
        if not pairs:
            logger.warning("No valid chunk texts for reranking")
            # Fallback: return top_n candidates by dense/sparse score
            fallback = sorted(candidates, key=lambda x: x['score'], reverse=True)[:self.top_n]
            for item in fallback:
                item["rerank_score"] = item["score"]
            return fallback
        
        # Score pairs using cross-encoder
        try:
            scores = self.model.predict(pairs, batch_size=self.batch_size)
        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            # Fallback: use dense/sparse scores
            fallback = sorted(candidates, key=lambda x: x['score'], reverse=True)[:self.top_n]
            for item in fallback:
                item["rerank_score"] = item["score"]
            return fallback
        
        # Attach rerank scores to candidates
        score_index = 0
        for candidate in candidates:
            if score_index < len(scores):
                candidate["rerank_score"] = float(scores[score_index])
                score_index += 1
            else:
                # Fallback to original score
                candidate["rerank_score"] = candidate["score"]
        
        # Sort by rerank score (descending)
        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        
        # Keep top-N
        top_n = reranked[:self.top_n]
        
        latency = time.time() - start_time
        logger.info(f"Reranking complete: {len(top_n)} chunks in {latency:.3f}s")
        
        # Log rerank scores
        for i, item in enumerate(top_n):
            logger.debug(
                f"  {i+1}. rerank_score={item['rerank_score']:.4f} "
                f"orig_score={item['score']:.4f} "
                f"type={item.get('retrieval_type', 'N/A')} "
                f"chunk_id={item['chunk_id']}"
            )
        
        return top_n


class Retriever:
    """
    Orchestrator class for hybrid retrieval pipeline.
    
    Responsibilities:
    - Call dense retriever
    - Call sparse retriever (via SparseIndexService)
    - Merge and deduplicate results
    - Call reranker
    - Return final chunks with rerank_score
    """
    
    def __init__(
        self,
        dense_top_k: int = None,
        sparse_top_k: int = None,
        max_candidates: int = None,
        rerank_top_n: int = None
    ):
        """
        Initialize retriever orchestrator.
        
        Args:
            dense_top_k: Number of candidates for dense retrieval (uses Config.RETRIEVER_CONFIG if None)
            sparse_top_k: Number of candidates for sparse retrieval (uses Config.RETRIEVER_CONFIG if None)
            max_candidates: Maximum candidates after merge (uses Config.RETRIEVER_CONFIG if None)
            rerank_top_n: Number of chunks to return after reranking (uses Config.RETRIEVER_CONFIG if None)
        """
        # Use config defaults if not specified
        config = Config.RETRIEVER_CONFIG
        if dense_top_k is None:
            dense_top_k = config.get("dense_top_k", 30)
        if sparse_top_k is None:
            sparse_top_k = config.get("sparse_top_k", 20)
        if max_candidates is None:
            max_candidates = config.get("max_candidates", 40)
        if rerank_top_n is None:
            rerank_top_n = config.get("rerank_top_n", 10)
        
        self.dense_top_k = dense_top_k
        self.sparse_top_k = sparse_top_k
        self.max_candidates = max_candidates
        self.rerank_top_n = rerank_top_n
        
        # Initialize dense retriever
        self.dense_retriever = DenseRetriever(
            qdrant_url="http://localhost:6333",
            collection_name="rag_chunks",
            embedding_model="openai/text-embedding-3-large",
            top_k=dense_top_k
        )
        
        # Initialize sparse index service (singleton)
        self.sparse_index_service = SparseIndexService()
        
        # Initialize hybrid merger (with config weights)
        self.hybrid_merger = HybridRetriever(
            max_candidates=max_candidates,
            dense_weight=config.get("dense_weight", 0.6),
            sparse_weight=config.get("sparse_weight", 0.4)
        )
        
        # Initialize cross-encoder reranker (uses Config.RERANKER_MODEL)
        self.reranker = CrossEncoderReranker(
            model_name=None,  # Uses Config.RERANKER_MODEL
            top_n=rerank_top_n
        )
        
        logger.info(
            f"Hybrid retriever initialized: "
            f"dense_k={dense_top_k}, sparse_k={sparse_top_k}, "
            f"max_candidates={max_candidates}, rerank_n={rerank_top_n}"
        )
    
    def preload_document(self, doc_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Preload document for sparse retrieval (delegates to SparseIndexService).
        
        Args:
            doc_id: Document ID
            chunks: List of chunks with "text" field
        """
        self.sparse_index_service.build_index(doc_id, chunks)
    
    def retrieve(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank chunks for a query using hybrid approach.
        
        Args:
            query: User query string
            session_id: Optional session_id for session isolation
            
        Returns:
            List of retrieved chunks sorted by rerank_score:
            [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "doc_id": "...",
                    "document_name": "...",
                    "page_numbers": [...],
                    "char_start": int,
                    "char_end": int,
                    "score": 0.92,
                    "rerank_score": 0.95,
                    "retrieval_type": "dense|sparse|hybrid"
                }
            ]
        """
        logger.info(f"Starting hybrid retrieval for query: '{query}' (session_id={session_id})")
        total_start = time.time()
        
        # Stage 1: Dense retrieval
        try:
            dense_results = self.dense_retriever.retrieve(query, session_id=session_id)
            logger.info(f"Stage 1 - Dense: {len(dense_results)} candidates")
        except RetrieverError as e:
            logger.error(f"Dense retrieval failed: {str(e)}")
            dense_results = []
        
        # Stage 2: Sparse retrieval (BM25)
        try:
            # Get unique doc_ids from dense results
            doc_ids = list(set(r["doc_id"] for r in dense_results))
            
            if doc_ids:
                sparse_results = self.sparse_index_service.retrieve(
                    query,
                    doc_ids=doc_ids,
                    top_k=self.sparse_top_k
                )
                logger.info(f"Stage 2 - Sparse: {len(sparse_results)} candidates")
            else:
                logger.warning("No doc_ids from dense results, skipping sparse retrieval")
                sparse_results = []
        except RetrieverError as e:
            logger.error(f"Sparse retrieval failed: {str(e)}")
            sparse_results = []
        
        # Stage 3: Hybrid merge
        try:
            merged_candidates = self.hybrid_merger.merge(dense_results, sparse_results)
            logger.info(f"Stage 3 - Merged: {len(merged_candidates)} candidates")
        except RetrieverError as e:
            logger.error(f"Hybrid merge failed: {str(e)}")
            merged_candidates = dense_results or []
        
        # Stage 4: Cross-encoder reranking
        try:
            reranked = self.reranker.rerank(query, merged_candidates)
            logger.info(f"Stage 4 - Reranked: {len(reranked)} chunks")
        except RetrieverError as e:
            logger.error(f"Reranking failed: {str(e)}")
            # Fallback: use merged results with original scores
            reranked = sorted(merged_candidates, key=lambda x: x["score"], reverse=True)[:self.rerank_top_n]
            for item in reranked:
                item["rerank_score"] = item["score"]
        
        # Deduplicate by chunk_id (final safety)
        results = []
        seen_chunks = set()
        
        for item in reranked:
            chunk_id = item["chunk_id"]
            
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)
            
            results.append(item)
            
            if len(results) >= self.rerank_top_n:
                break
        
        total_latency = time.time() - total_start
        logger.info(f"Retrieval complete: {len(results)} chunks in {total_latency:.3f}s")
        logger.info(f"  Dense: {len(dense_results)}, Sparse: {len(sparse_results)}, Merged: {len(merged_candidates)}, Final: {len(results)}")
        
        return results
    
    def retrieve_multi_query(
        self,
        sub_queries: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Retrieve chunks for each sub-query.
        
        CRITICAL: Assign each chunk to its sub_query_id for tracking.
        
        Works for:
        - Single query (sub_queries length = 1)
        - Multiple queries (sub_queries length > 1)
        - Single document (chunks from 1 doc)
        - Multiple documents (chunks from multiple docs)
        
        NO DOCUMENT FILTERING - Retrieve broadly for each sub-query.
        
        Args:
            sub_queries: List from LLM decomposer
                [
                    {
                        "id": 0,
                        "question": "Complete question",
                        "original_text": "Text from original query"
                    },
                    ...
                ]
            session_id: Session ID
            
        Returns:
            Dict: {sub_query_id: [chunks_with_tags]}
                {
                    0: [
                        {
                            "chunk_id": "...",
                            "text": "...",
                            "doc_id": "...",
                            "document_name": "...",
                            "page_numbers": [...],
                            "char_start": int,
                            "char_end": int,
                            "score": 0.92,
                            "rerank_score": 0.95,
                            "retrieval_type": "dense|sparse|hybrid",
                            "sub_query_id": 0,
                            "sub_query_text": "Complete question",
                            "original_query_text": "Text from original query"
                        }
                    ],
                    1: [...]
                }
        """
        logger.info(f"Starting multi-query retrieval for {len(sub_queries)} sub-queries")
        results_by_query = {}
        
        for sub_query in sub_queries:
            query_id = sub_query["id"]
            question_text = sub_query["question"]
            original_text = sub_query["original_text"]
            
            logger.info(f"Retrieving for sub-query {query_id}: '{question_text[:50]}...'")
            
            # Use existing retrieve() method - NO changes needed!
            # This preserves all hybrid logic (dense + sparse + rerank)
            chunks = self.retrieve(question_text, session_id=session_id)
            
            # CRITICAL: Tag each chunk with sub_query metadata
            for chunk in chunks:
                chunk["sub_query_id"] = query_id
                chunk["sub_query_text"] = question_text
                chunk["original_query_text"] = original_text
            
            results_by_query[query_id] = chunks
            
            logger.info(f"Sub-query {query_id}: Retrieved {len(chunks)} chunks")
        
        # Log summary
        total_chunks = sum(len(chunks) for chunks in results_by_query.values())
        logger.info(f"Multi-query retrieval complete: {total_chunks} chunks from {len(results_by_query)} sub-queries")
        
        return results_by_query


# =============================================================================
# Test Method (Manual Verification)
# =============================================================================

if __name__ == "__main__":
    """
    Test hybrid retriever with a sample query.
    
    Usage:
        python modules/retriever.py
    """
    logging.basicConfig(level=logging.INFO)
    
    retriever = Retriever(
        dense_top_k=40,
        sparse_top_k=40,
        max_candidates=60,
        rerank_top_n=6
    )
    
    results = retriever.retrieve("financial risks")
    
    print("\n=== Hybrid Retrieval Results ===")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Chunk ID: {result['chunk_id']}")
        print(f"   Type: {result['retrieval_type']}")
        print(f"   Score: {result['score']:.4f}")
        print(f"   Rerank Score: {result['rerank_score']:.4f}")
        print(f"   Doc: {result['doc_id']}")
        print(f"   Document: {result['document_name']}")
        print(f"   Pages: {result['page_numbers']}")
        print(f"   Text Preview: {result['text'][:200]}...")