"""
Sparse Index Service - BM25 Index Management

Manages BM25 indices for sparse keyword retrieval.
Builds indices during document upload and provides fast keyword search.

Responsibilities:
- Build BM25 indices from chunk texts
- Cache indices by doc_id (in-memory)
- Perform keyword search with BM25 scoring
- Provide clean interface for retriever

Author: Yottanest Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SparseIndexService:
    """
    Singleton service for managing BM25 sparse indices.
    
    Responsibilities:
    - Build BM25 index per document
    - Cache indices in memory (fast access)
    - Provide keyword search functionality
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(SparseIndexService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize sparse index service."""
        if self._initialized:
            return
        
        self._initialized = True
        
        # BM25 index cache: {doc_id: {"index": BM25Okapi, "chunks": List}}
        self.index_cache: Dict[str, Dict[str, Any]] = {}
        
        try:
            from rank_bm25 import BM25Okapi
            self.BM25Okapi = BM25Okapi
            logger.info("Sparse index service initialized with BM25")
        except ImportError:
            logger.error("rank_bm25 not installed. Install with: pip install rank-bm25")
            raise
    
    def build_index(self, doc_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Build and cache BM25 index for a document.
        
        Args:
            doc_id: Document ID
            chunks: List of chunks with "text" field
        """
        if not chunks:
            logger.warning(f"No chunks to index for doc_id={doc_id}")
            return
        
        logger.info(f"Building BM25 index for doc_id={doc_id}: {len(chunks)} chunks")
        
        try:
            # Tokenize: simple .lower().split()
            corpus = []
            for chunk in chunks:
                text = chunk.get("text", "")
                tokens = text.lower().split()
                corpus.append(tokens)
            
            # Build BM25 index
            index = self.BM25Okapi(corpus)
            
            # Cache index
            self.index_cache[doc_id] = {
                "index": index,
                "chunks": chunks
            }
            
            logger.info(f"BM25 index built and cached for doc_id={doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to build BM25 index for {doc_id}: {str(e)}")
            raise
    
    def retrieve(
        self,
        query: str,
        doc_ids: List[str],
        top_k: int = 40
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-K candidates using BM25 keyword search.
        
        Args:
            query: User query string
            doc_ids: List of document IDs to search
            top_k: Number of candidates to return
            
        Returns:
            List of candidates with BM25 scores:
            {
                "chunk_id": str,
                "text": str,
                "doc_id": str,
                "document_name": str,
                "page_numbers": list,
                "char_start": int,
                "char_end": int,
                "score": float,
                "retrieval_type": "sparse"
            }
        """
        logger.info(f"Sparse retrieval for query: '{query}' ({len(doc_ids)} docs)")
        
        if not self.index_cache:
            logger.warning("No BM25 indices cached")
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        all_candidates = []
        
        # Search across all indexed documents
        for doc_id in doc_ids:
            if doc_id not in self.index_cache:
                logger.debug(f"No BM25 index for doc_id={doc_id}")
                continue
            
            index_data = self.index_cache[doc_id]
            index = index_data["index"]
            chunks = index_data["chunks"]
            
            # Get BM25 scores
            scores = index.get_scores(query_tokens)
            
            # Build candidates
            for chunk_idx, score in enumerate(scores):
                if score <= 0:
                    continue
                
                chunk = chunks[chunk_idx]
                candidate = {
                    "chunk_id": chunk.get("chunk_id", ""),
                    "text": chunk.get("text", ""),
                    "doc_id": chunk.get("doc_id", ""),
                    "document_name": chunk.get("document_name", ""),
                    "page_numbers": chunk.get("page_numbers", []),
                    "char_start": chunk.get("char_start", 0),
                    "char_end": chunk.get("char_end", 0),
                    "score": float(score),
                    "retrieval_type": "sparse"
                }
                all_candidates.append(candidate)
        
        # Sort by BM25 score (descending) and take top_k
        all_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_k = all_candidates[:top_k]
        
        logger.info(f"Sparse retrieval: {len(top_k)} candidates returned")
        
        return top_k
    
    def has_index(self, doc_id: str) -> bool:
        """
        Check if BM25 index exists for a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if index exists, False otherwise
        """
        return doc_id in self.index_cache
    
    def get_indexed_docs(self) -> List[str]:
        """
        Get list of all document IDs with indexed documents.
        
        Returns:
            List of document IDs
        """
        return list(self.index_cache.keys())