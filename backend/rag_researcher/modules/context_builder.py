"""
Context Builder Module

Builds structured context from retrieved chunks.

Responsibilities:
- Extract relevant information from retrieved chunks
- Maintain order by relevance
- Deduplicate chunks
- Respect context token limits
- Preserve metadata

Author: Yottanest Team
Version: 1.0.0
"""
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds structured context from retrieved chunks."""
    
    # Approximate token count per character (for English text)
    CHARS_PER_TOKEN = 4
    # Maximum context tokens for gpt-4o-mini (leave room for system prompt + response)
    MAX_CONTEXT_TOKENS = 120000  # gpt-4o-mini has 128K context, leave buffer
    
    def __init__(self, max_tokens: int = MAX_CONTEXT_TOKENS):
        """
        Initialize context builder.
        
        Args:
            max_tokens: Maximum tokens for context window
        """
        self.max_tokens = max_tokens
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Simple approximation: chars / 4
        return len(text) // ContextBuilder.CHARS_PER_TOKEN
    
    def build(self, chunks: List[Dict], max_tokens: Optional[int] = None) -> List[Dict]:
        """
        Build structured context from retrieved chunks.
        
        Args:
            chunks: List of retrieved chunks from retriever
            max_tokens: Optional override for max tokens
            
        Returns:
            List of structured context items
        """
        if not chunks:
            logger.warning("No chunks provided for context building")
            return []
        
        max_tokens = max_tokens or self.max_tokens
        context_items = []
        total_tokens = 0
        seen_chunk_ids = set()
        
        # Process chunks in order (already sorted by rerank_score DESC)
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id")
            
            # Skip duplicates
            if chunk_id in seen_chunk_ids:
                logger.debug(f"Skipping duplicate chunk: {chunk_id}")
                continue
            
            # Get text from payload
            text = chunk.get("text", "")
            if not text:
                logger.warning(f"Chunk {chunk_id} has no text, skipping")
                continue
            
            # Estimate tokens for this chunk
            chunk_tokens = self.estimate_tokens(text)
            
            # Check if adding this chunk exceeds token limit
            if total_tokens + chunk_tokens > max_tokens:
                logger.info(f"Token limit reached ({total_tokens}/{max_tokens}), stopping at {i} chunks")
                break
            
            # Build context item (NO string concatenation, just structure)
            context_item = {
                "chunk_id": chunk_id,
                "text": text,
                "source": chunk.get("payload", {}).get("document_name", "Unknown"),
                "score": chunk.get("rerank_score", chunk.get("score", 0.0)),
                "metadata": {
                    "page_numbers": chunk.get("payload", {}).get("page_numbers", []),
                    "chunk_index": chunk.get("payload", {}).get("chunk_index", 0),
                    "strategy": chunk.get("payload", {}).get("strategy", "unknown"),
                    "doc_id": chunk.get("payload", {}).get("doc_id", ""),
                    "section_hint": chunk.get("payload", {}).get("section_hint", ""),
                }
            }
            
            context_items.append(context_item)
            total_tokens += chunk_tokens
            seen_chunk_ids.add(chunk_id)
            
            logger.debug(f"Added chunk {chunk_id} ({chunk_tokens} tokens, total: {total_tokens})")
        
        logger.info(f"Built context with {len(context_items)} chunks ({total_tokens} tokens)")
        return context_items
    
    def validate_context(self, context: List[Dict]) -> bool:
        """
        Validate context items.
        
        Args:
            context: List of context items
            
        Returns:
            True if valid, False otherwise
        """
        if not context:
            logger.error("Context is empty")
            return False
        
        required_fields = ["chunk_id", "text", "source", "score"]
        
        for item in context:
            for field in required_fields:
                if field not in item:
                    logger.error(f"Context item missing required field: {field}")
                    return False
            
            if not item["text"]:
                logger.error(f"Context item {item['chunk_id']} has empty text")
                return False
        
        return True
    
    def build_multi_query_context(
        self,
        results_by_query: Dict[int, List[Dict[str, Any]]],
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Build context from multi-query results.
        
        Groups chunks by sub-query for clear LLM guidance.
        
        Args:
            results_by_query: {sub_query_id: [chunks]} from retriever.retrieve_multi_query()
            max_tokens: Optional override for max tokens
            
        Returns:
            Flattened context with query metadata
        """
        if not results_by_query:
            logger.warning("No multi-query results provided for context building")
            return []
        
        max_tokens = max_tokens or self.max_tokens
        
        # Flatten all chunks, preserving sub_query_id tags
        all_chunks = []
        for query_id, chunks in results_by_query.items():
            for chunk in chunks:
                all_chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "source": chunk.get("document_name", "Unknown"),
                    "score": chunk.get("rerank_score", chunk.get("score", 0.0)),
                    "metadata": {
                        "page_numbers": chunk.get("page_numbers", []),
                        "sub_query_id": chunk.get("sub_query_id", 0),
                        "sub_query_text": chunk.get("sub_query_text", ""),
                        "original_query_text": chunk.get("original_query_text", ""),
                        "rerank_score": chunk.get("rerank_score", 0.0),
                        "retrieval_type": chunk.get("retrieval_type", "unknown")
                    }
                })
        
        # Sort by rerank_score (global ranking)
        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        # Detect scenario: single query vs multi-query
        sub_query_ids = set(chunk["metadata"]["sub_query_id"] for chunk in all_chunks)
        is_multi_query = len(sub_query_ids) > 1
        
        if is_multi_query:
            # Multi-query: Ensure diversity across sub-queries
            context = self._limit_with_diversity(all_chunks, max_tokens)
        else:
            # Single query: Take top by score (NO diversity needed)
            context = self._take_top_by_score(all_chunks, max_tokens)
        
        logger.info(
            f"Built multi-query context: {len(context)} chunks "
            f"from {len(results_by_query)} sub-queries "
            f"({'multi-query' if is_multi_query else 'single-query'})"
        )
        
        return context
    
    def _limit_with_diversity(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> List[Dict[str, Any]]:
        """
        Limit chunks while preserving diversity across sub-queries.
        
        Ensures we don't take all chunks from just one sub-query.
        Only applied for multi-query scenarios.
        
        Args:
            chunks: All chunks sorted by score
            max_tokens: Maximum tokens
            
        Returns:
            Filtered chunks with diversity
        """
        if not chunks:
            return []
        
        selected = []
        tokens = 0
        query_counts = {}  # Track chunks per sub-query
        
        for chunk in chunks:
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            chunk_tokens = len(chunk["text"]) / self.CHARS_PER_TOKEN
            
            if tokens + chunk_tokens > max_tokens:
                break
            
            # Diversity check: don't take too many from one sub-query
            query_id = chunk["metadata"]["sub_query_id"]
            query_count = query_counts.get(query_id, 0)
            
            # Max 8 chunks per sub-query (unless it's the only one)
            if len(set(query_counts.keys())) > 1 and query_count >= 8:
                continue
            
            selected.append(chunk)
            tokens += chunk_tokens
            query_counts[query_id] = query_count + 1
        
        logger.info(f"Diversity selection (multi-query): {query_counts}")
        
        return selected
    
    def _take_top_by_score(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> List[Dict[str, Any]]:
        """
        Take top chunks by rerank_score.
        
        Used for single-query scenarios where diversity is NOT needed.
        
        All from same document? Fine!
        All from different docs? Fine!
        Let scores decide.
        
        Args:
            chunks: All chunks sorted by rerank_score DESC
            max_tokens: Maximum tokens
            
        Returns:
            Top chunks by score
        """
        if not chunks:
            return []
        
        selected = []
        tokens = 0
        
        for chunk in chunks:  # Already sorted by score
            chunk_tokens = len(chunk["text"]) / self.CHARS_PER_TOKEN
            
            if tokens + chunk_tokens > max_tokens:
                break
            
            selected.append(chunk)
            tokens += chunk_tokens
        
        logger.info(f"Top-score selection (single-query): {len(selected)} chunks")
        
        return selected