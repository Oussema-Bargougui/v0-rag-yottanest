"""
Similarity Cluster Chunker - OLD Working Method (per RAG_CHUNKING_PIPELINE.md Strategy 2)

Production-grade chunking based on sentence-level similarity matrix clustering.
Groups sentences into semantic clusters using similarity thresholding.

ALGORITHM (EXACT FROM RAG_CHUNKING_PIPELINE.md):
1. Split full_text into sentences
2. Embed all sentences
3. Build similarity matrix
4. Use threshold (e.g. 0.75)
5. Build clusters by adjacency
6. Merge sentences per cluster
7. Enforce max_tokens/min_tokens
8. Preserve order of clusters

This is the OLD WORKING method.
"""

import uuid
from typing import List, Dict, Any, Tuple
import numpy as np
from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)


class SimilarityClusterChunker:
    """
    Chunks documents based on sentence-level similarity matrix clustering.
    
    ALGORITHM (per RAG_CHUNKING_PIPELINE.md Strategy 2):
    1. Split full_text into sentences
    2. Embed all sentences
    3. Build similarity matrix
    4. Use threshold (e.g. 0.75)
    5. Build clusters by adjacency
    6. Merge sentences per cluster
    7. Enforce max_tokens/min_tokens
    8. Preserve order of clusters
    """
    
    # Safety limits
    MAX_CHUNK_CHARS = 1200  # Maximum characters per chunk
    MIN_CHUNK_CHARS = 400   # Minimum characters per chunk
    MAX_SENTENCES = 5000     # Prevent infinite loops
    EMBEDDING_BATCH_SIZE = 100
    
    def __init__(
        self,
        similarity_threshold: float = 0.75,
        embedding_model: str = None
    ):
        """
        Initialize similarity cluster chunker.
        
        Args:
            similarity_threshold: Threshold for clustering sentences (0-1)
            embedding_model: Name of embedding model to use
        """
        self.similarity_threshold = similarity_threshold
        
        # Initialize embedding client
        if embedding_model is None:
            embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        self.embedding_model = embedding_model
        self.client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            default_headers={
                "HTTP-Referer": "https://yottanest.com",
                "X-Title": "Yottanest RAG"
            }
        )
    
    def _split_sentences_with_offsets(
        self,
        text: str
    ) -> List[Tuple[str, int, int]]:
        """
        Split text into sentences with exact character offsets.
        
        Args:
            text: Full document text
            
        Returns:
            List of (sentence_text, start_char, end_char) tuples
        """
        sentences = []
        i = 0
        n = len(text)
        
        while i < n:
            # Skip whitespace
            while i < n and text[i].isspace():
                i += 1
            
            if i >= n:
                break
            
            # Find sentence start
            sent_start = i
            
            # Find sentence end
            while i < n:
                if text[i] in '.!?':
                    i += 1
                    # Skip trailing whitespace
                    while i < n and text[i].isspace():
                        i += 1
                    
                    # Extract sentence
                    sentence_text = text[sent_start:i].strip()
                    
                    if sentence_text:
                        sentences.append((sentence_text, sent_start, i))
                    
                    # Safety: prevent infinite loop
                    if len(sentences) > self.MAX_SENTENCES:
                        logger.warning(f"Hit MAX_SENTENCES limit: {self.MAX_SENTENCES}")
                        return sentences
                    
                    break
                else:
                    i += 1
            
            # If we didn't find a sentence end, break
            if i >= n:
                # Try to add remaining text as sentence
                remaining = text[sent_start:].strip()
                if remaining and len(remaining) > 10:
                    sentences.append((remaining, sent_start, n))
                break
        
        return sentences
    
    def _embed_texts_batched(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using batching.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            NumPy array of embeddings
        """
        embeddings = []
        
        for i in range(0, len(texts), self.EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + self.EMBEDDING_BATCH_SIZE]
            
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                
                for item in response.data:
                    embeddings.append(np.array(item.embedding))
                    
            except Exception as e:
                logger.warning(f"Batch embedding failed, falling back to one-by-one: {str(e)}")
                for text in batch:
                    try:
                        response = self.client.embeddings.create(
                            model=self.embedding_model,
                            input=text
                        )
                        embeddings.append(np.array(response.data[0].embedding))
                    except Exception as e2:
                        logger.error(f"Failed to embed text: {str(e2)}")
                        embeddings.append(np.zeros(1536))
        
        return np.array(embeddings)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _build_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Build similarity matrix from embeddings.
        
        Args:
            embeddings: Sentence embeddings (N x D)
            
        Returns:
            N x N similarity matrix
        """
        n = len(embeddings)
        sim_matrix = np.zeros((n, n))
        
        # Compute pairwise similarities
        for i in range(n):
            for j in range(n):
                if i < j:
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    sim_matrix[i][j] = sim
                    sim_matrix[j][i] = sim
                elif i == j:
                    sim_matrix[i][j] = 1.0  # Self-similarity
        
        return sim_matrix
    
    def _build_clusters_by_adjacency(
        self,
        sim_matrix: np.ndarray,
        n_sentences: int
    ) -> List[List[int]]:
        """
        Build clusters using similarity threshold and adjacency.
        
        Args:
            sim_matrix: N x N similarity matrix
            n_sentences: Number of sentences
            
        Returns:
            List of clusters, where each cluster is a list of sentence indices
        """
        clusters = []
        i = 0
        
        while i < n_sentences:
            # Start new cluster
            cluster = [i]
            
            # Expand forward while similarity is above threshold
            while i + 1 < n_sentences:
                # Compare last in cluster with next sentence
                last_in_cluster = cluster[-1]
                next_sent = i + 1
                
                sim = sim_matrix[last_in_cluster][next_sent]
                
                # If similar enough, add to cluster
                if sim >= self.similarity_threshold:
                    cluster.append(i + 1)
                    i += 1
                else:
                    break
            
            clusters.append(cluster)
            i += 1
        
        return clusters
    
    def _get_pages_for_chunk(
        self,
        chunk_start: int,
        chunk_end: int,
        page_map: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Get list of page numbers that overlap with a chunk.
        
        Args:
            chunk_start: Start character index of chunk
            chunk_end: End character index of chunk
            page_map: Page mapping from document stream
            
        Returns:
            List of page numbers
        """
        chunk_pages = []
        for page in page_map:
            # Check if page overlaps with chunk
            if not (page["end_char"] <= chunk_start or page["start_char"] >= chunk_end):
                if page["page_number"] not in chunk_pages:
                    chunk_pages.append(page["page_number"])
        
        return sorted(chunk_pages)
    
    def _enforce_chunk_size_limits(
        self,
        sentences: List[Tuple[str, int, int]],
        page_map: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enforce MIN_CHUNK_CHARS and MAX_CHUNK_CHARS limits.
        
        Args:
            sentences: List of (text, start, end) tuples
            page_map: Page mapping
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        current_chunk_sentences = []
        current_chunk_text = ""
        current_chunk_start = 0
        
        for sent_text, sent_start, sent_end in sentences:
            # Calculate size if we add this sentence
            test_chunk = current_chunk_text + " " + sent_text if current_chunk_text else sent_text
            
            # If adding this sentence would exceed limit, create chunk first
            if len(test_chunk) > self.MAX_CHUNK_CHARS and current_chunk_sentences:
                # Create chunk with current sentences
                chunk_text = current_chunk_text
                chunk_start_char = current_chunk_start
                chunk_end_char = current_chunk_sentences[-1][2]
                
                # Get page numbers
                page_numbers = self._get_pages_for_chunk(
                    chunk_start_char, chunk_end_char, page_map
                )
                
                chunks.append({
                    "text": chunk_text,
                    "page_numbers": page_numbers,
                    "char_range": [chunk_start_char, chunk_end_char],
                    "chunk_size": len(chunk_text)
                })
                
                # Start new chunk with current sentence
                current_chunk_sentences = [(sent_text, sent_start, sent_end)]
                current_chunk_text = sent_text
                current_chunk_start = sent_start
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append((sent_text, sent_start, sent_end))
                current_chunk_text = test_chunk
                
                # Set start if first sentence
                if not current_chunk_sentences[:-1]:
                    current_chunk_start = sent_start
        
        # Add remaining
        if current_chunk_sentences:
            chunk_text = current_chunk_text
            chunk_start_char = current_chunk_start
            chunk_end_char = current_chunk_sentences[-1][2]
            
            page_numbers = self._get_pages_for_chunk(
                chunk_start_char, chunk_end_char, page_map
            )
            
            chunks.append({
                "text": chunk_text,
                "page_numbers": page_numbers,
                "char_range": [chunk_start_char, chunk_end_char],
                "chunk_size": len(chunk_text)
            })
        
        # Merge chunks that are too small
        i = 0
        while i < len(chunks) - 1:
            current = chunks[i]
            next_chunk = chunks[i + 1]
            
            if current["chunk_size"] < self.MIN_CHUNK_CHARS:
                # Merge with next chunk
                merged_text = current["text"] + " " + next_chunk["text"]
                merged_start = current["char_range"][0]
                merged_end = next_chunk["char_range"][1]
                
                merged_pages = list(set(current["page_numbers"] + next_chunk["page_numbers"]))
                merged_pages.sort()
                
                chunks[i] = {
                    "text": merged_text,
                    "page_numbers": merged_pages,
                    "char_range": [merged_start, merged_end],
                    "chunk_size": len(merged_text)
                }
                
                chunks.pop(i + 1)
            else:
                i += 1
        
        return chunks
    
    def _extract_metadata(self, document_data: Dict[str, Any], doc_id: str) -> Dict[str, str]:
        """
        Extract metadata from document_data.
        
        Args:
            document_data: Document dictionary
            doc_id: Document ID
            
        Returns:
            Dictionary with metadata fields
        """
        metadata = {}
        
        # Required fields - use "unknown" only if missing
        if "document_name" in document_data and document_data["document_name"]:
            metadata["document_name"] = document_data["document_name"]
        else:
            logger.warning(f"Missing 'document_name' for {doc_id}")
            metadata["document_name"] = "unknown"
        
        if "extraction_version" in document_data and document_data["extraction_version"]:
            metadata["extraction_version"] = document_data["extraction_version"]
        else:
            logger.warning(f"Missing 'extraction_version' for {doc_id}")
            metadata["extraction_version"] = "unknown"
        
        if "ingestion_timestamp" in document_data and document_data["ingestion_timestamp"]:
            metadata["ingestion_timestamp"] = document_data["ingestion_timestamp"]
        else:
            logger.warning(f"Missing 'ingestion_timestamp' for {doc_id}")
            metadata["ingestion_timestamp"] = "unknown"
        
        if "source" in document_data and document_data["source"]:
            metadata["source"] = document_data["source"]
        else:
            logger.warning(f"Missing 'source' for {doc_id}")
            metadata["source"] = "unknown"
        
        # Optional fields - only add if present
        if "file_type" in document_data:
            metadata["file_type"] = document_data["file_type"]
        
        if "file_size" in document_data:
            metadata["file_size"] = document_data["file_size"]
        
        if "file_hash" in document_data:
            metadata["file_hash"] = document_data["file_hash"]
        
        return metadata
    
    def chunk_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chunk a document using sentence-level similarity matrix clustering.
        
        ALGORITHM (per RAG_CHUNKING_PIPELINE.md Strategy 2):
        1. Split full_text into sentences
        2. Embed all sentences
        3. Build similarity matrix
        4. Use threshold (e.g. 0.75)
        5. Build clusters by adjacency
        6. Merge sentences per cluster
        7. Enforce max_tokens/min_tokens
        8. Preserve order of clusters
        
        Args:
            document_data: Document dictionary with 'doc_id', 'pages', and metadata
            
        Returns:
            Dictionary with 'chunks' list and metadata
        """
        doc_id = document_data["doc_id"]
        pages = document_data["pages"]
        
        # Extract metadata
        metadata = self._extract_metadata(document_data, doc_id)
        
        logger.info(f"Starting similarity matrix clustering for {doc_id}")
        
        # Step 1: Build document stream
        full_text = ""
        page_map = []
        
        for page in pages:
            start = len(full_text)
            full_text += page["text"] + "\n\n"
            end = len(full_text)
            
            page_map.append({
                "page_number": page["page_number"],
                "start_char": start,
                "end_char": end
            })
        
        # Step 2: Split into sentences
        sentences = self._split_sentences_with_offsets(full_text)
        sentence_count = len(sentences)
        
        logger.info(f"Document has {sentence_count} sentences")
        
        if sentence_count == 0:
            return {
                "doc_id": doc_id,
                "document_name": metadata.get("document_name", "unknown"),
                "chunk_strategy": "similarity_cluster",
                "chunks": []
            }
        
        # Safety: enforce max sentences limit
        if sentence_count > self.MAX_SENTENCES:
            logger.warning(f"Truncating from {sentence_count} to {self.MAX_SENTENCES} sentences")
            sentences = sentences[:self.MAX_SENTENCES]
            sentence_count = self.MAX_SENTENCES
        
        # Step 3: Embed sentences (batched)
        sentence_texts = [s[0] for s in sentences]
        logger.info(f"Embedding {sentence_count} sentences in batches of {self.EMBEDDING_BATCH_SIZE}")
        
        start_time = time.time()
        embeddings = self._embed_texts_batched(sentence_texts)
        embedding_time = time.time() - start_time
        
        logger.info(f"Embeddings generated in {embedding_time:.2f}s")
        
        # Step 4: Build similarity matrix
        logger.info("Building similarity matrix...")
        sim_matrix = self._build_similarity_matrix(embeddings)
        
        # Step 5: Build clusters by adjacency
        logger.info(f"Building clusters with threshold {self.similarity_threshold}...")
        clusters = self._build_clusters_by_adjacency(sim_matrix, sentence_count)
        
        logger.info(f"Created {len(clusters)} clusters")
        
        # Step 6: Merge sentences per cluster and enforce size limits
        chunks = []
        
        for cluster in clusters:
            # Extract sentences for this cluster
            cluster_sentences = [sentences[i] for i in cluster]
            
            # Merge into chunks with size enforcement
            cluster_chunks = self._enforce_chunk_size_limits(cluster_sentences, page_map)
            chunks.extend(cluster_chunks)
        
        logger.info(f"After size enforcement: {len(chunks)} chunks")
        
        # Build final chunk dictionaries with metadata
        chunks_dict = []
        
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                "chunk_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "text": chunk["text"],
                "strategy": "similarity_cluster",
                "page_numbers": chunk["page_numbers"],
                "char_range": chunk["char_range"],
                "position": i,
                "chunk_size": chunk["chunk_size"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                **metadata
            }
            chunks_dict.append(chunk_dict)
        
        logger.info(f"Created {len(chunks_dict)} final chunks (avg {np.mean([c['chunk_size'] for c in chunks_dict]):.0f} chars)")
        
        return {
            "doc_id": doc_id,
            "document_name": metadata.get("document_name", "unknown"),
            "chunk_strategy": "similarity_cluster",
            "chunks": chunks_dict
        }


# Import time for performance logging
import time