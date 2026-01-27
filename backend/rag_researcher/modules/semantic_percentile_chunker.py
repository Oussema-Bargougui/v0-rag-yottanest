"""
Semantic Percentile Chunker

Production-grade chunking based on semantic density.
Creates chunk boundaries where semantic similarity drops below a percentile threshold.

This is NOT a page-based chunker. It operates on full document stream.
Enhanced for legal documents with boundary-aware splitting and metadata extraction.
"""

import uuid
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from openai import OpenAI
import os
import re
import logging
from config import Config

logger = logging.getLogger(__name__)


class SemanticPercentileChunker:
    """
    Chunks documents based on semantic density using percentile-based thresholding.
    """
    
    # Safety limits
    MAX_SENTENCES_PER_DOC = 5000
    MAX_CHUNKS_PER_DOC = 500
    EMBEDDING_BATCH_SIZE = 100
    
    def __init__(
        self,
        min_tokens: int = 150,
        max_tokens: int = 800,
        percentile_threshold: float = 25.0,
        embedding_model: str = None
    ):
        """
        Initialize the semantic percentile chunker.
        
        Args:
            min_tokens: Minimum tokens per chunk
            max_tokens: Maximum tokens per chunk
            percentile_threshold: Percentile (0-100) for similarity drop threshold
            embedding_model: Name of embedding model to use
        """
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.percentile_threshold = percentile_threshold
        
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
    
    def _split_sentences_with_offsets(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into sentences with exact character offsets.
        
        This is CRITICAL for traceability, citations, and highlighting.
        Offsets MUST map 1:1 to original text.
        
        Args:
            text: Full document text
            
        Returns:
            List of (sentence_text, start_char, end_char) tuples
        """
        sentences = []
        start = 0
        i = 0
        n = len(text)
        
        while i < n:
            # Skip whitespace at start
            while i < n and text[i].isspace():
                i += 1
                start = i
            
            if i >= n:
                break
            
            # Find sentence end: . ! ? or \n\n
            while i < n:
                char = text[i]
                
                # Sentence boundary
                if char in '.!?':
                    # Include the punctuation
                    i += 1
                    # Skip trailing spaces
                    while i < n and text[i].isspace():
                        i += 1
                    # End of sentence
                    sentence_text = text[start:i].strip()
                    if sentence_text:
                        sentences.append((sentence_text, start, i))
                    start = i
                    break
                # Paragraph boundary (two newlines)
                elif char == '\n':
                    # Check if next char is also newline
                    if i + 1 < n and text[i + 1] == '\n':
                        i += 2
                        while i < n and text[i].isspace():
                            i += 1
                        sentence_text = text[start:i].strip()
                        if sentence_text:
                            sentences.append((sentence_text, start, i))
                        start = i
                        break
                    else:
                        i += 1
                else:
                    i += 1
            
            # Safety: prevent infinite loop
            if len(sentences) > self.MAX_SENTENCES_PER_DOC:
                logger.warning(f"Hit MAX_SENTENCES_PER_DOC limit: {self.MAX_SENTENCES_PER_DOC}")
                break
        
        return sentences
    
    def _embed_texts_batched(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using batching.
        
        This is CRITICAL for performance and cost.
        Batching reduces API calls from N to N/batch_size.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            NumPy array of embeddings
        """
        embeddings = []
        
        # Process in batches
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
                # If batch fails, embed one-by-one as fallback
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
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Approximation: word count.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text.split())
    
    def _build_document_stream(self, pages: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Merge pages into a single text stream with character mapping.
        
        Args:
            pages: List of page dictionaries with 'text' and 'page_number'
            
        Returns:
            Tuple of (full_text, page_map)
        """
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
        
        return full_text, page_map
    
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
            if not (page["end_char"] <= chunk_start or page["start_char"] >= chunk_end):
                # Page overlaps with chunk
                if page["page_number"] not in chunk_pages:
                    chunk_pages.append(page["page_number"])
        
        return sorted(chunk_pages)
    
    def _extract_metadata(self, document_data: Dict[str, Any], doc_id: str) -> Dict[str, str]:
        """
        Extract metadata from document_data.
        
        CRITICAL: Use existing metadata if present, ONLY use defaults if missing.
        NEVER overwrite valid metadata with "unknown".
        
        Args:
            document_data: Document dictionary
            doc_id: Document ID
            
        Returns:
            Dictionary with metadata fields
        """
        metadata = {}
        
        # document_name - only use "unknown" if NOT present
        if "document_name" in document_data and document_data["document_name"]:
            metadata["document_name"] = document_data["document_name"]
        else:
            logger.warning(f"Missing 'document_name' for {doc_id}")
            metadata["document_name"] = "unknown"
        
        # extraction_version - only use "unknown" if NOT present
        if "extraction_version" in document_data and document_data["extraction_version"]:
            metadata["extraction_version"] = document_data["extraction_version"]
        else:
            logger.warning(f"Missing 'extraction_version' for {doc_id}")
            metadata["extraction_version"] = "unknown"
        
        # ingestion_timestamp - only use "unknown" if NOT present
        if "ingestion_timestamp" in document_data and document_data["ingestion_timestamp"]:
            metadata["ingestion_timestamp"] = document_data["ingestion_timestamp"]
        else:
            logger.warning(f"Missing 'ingestion_timestamp' for {doc_id}")
            metadata["ingestion_timestamp"] = "unknown"
        
        # source - only use "unknown" if NOT present
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
    
    def _detect_recommendation_boundary(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Detect if text is a recommendation boundary (header).
        
        For legal documents like FATF Recommendations, headers like:
        - "Recommendation 10"
        - "Interpretive Note 10"
        - "10. Financial institutions should..."
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (is_boundary, recommendation_number, recommendation_title)
        """
        # Pattern 1: "Recommendation X"
        rec_pattern = r'Recommendation\s+(\d+)[:\.\-]?\s*(.+)'
        match = re.match(rec_pattern, text, re.IGNORECASE)
        if match:
            rec_num = match.group(1)
            rec_title = match.group(2).strip() if match.group(2) else None
            return True, rec_num, rec_title
        
        # Pattern 2: "Interpretive Note X"
        note_pattern = r'Interpretive\s+Note\s+(\d+)[:\.\-]?\s*(.+)'
        match = re.match(note_pattern, text, re.IGNORECASE)
        if match:
            rec_num = match.group(1)
            rec_title = f"Interpretive Note {rec_num}"
            return True, rec_num, rec_title
        
        # Pattern 3: Numbered at start (e.g., "10. Financial institutions should...")
        num_pattern = r'^(\d+)\.\s+(.+)'
        match = re.match(num_pattern, text)
        if match:
            rec_num = match.group(1)
            rec_title = match.group(2).strip()[:100]  # First 100 chars as title
            return True, rec_num, rec_title
        
        return False, None, None
    
    def _extract_recommendation_metadata(self, chunk_text: str, chunk_start: int, sentences_with_offsets: List[Tuple[str, int, int]]) -> Dict[str, Any]:
        """
        Extract recommendation-specific metadata from chunk text.
        
        Args:
            chunk_text: Full chunk text
            chunk_start: Start character offset in document
            sentences_with_offsets: All sentences with offsets
            
        Returns:
            Dictionary with recommendation metadata
        """
        metadata = {}
        
        # Look for recommendation header in first 200 characters
        preview = chunk_text[:200] if len(chunk_text) > 200 else chunk_text
        is_boundary, rec_num, rec_title = self._detect_recommendation_boundary(preview)
        
        if is_boundary:
            metadata["recommendation_number"] = rec_num
            if rec_title:
                metadata["recommendation_title"] = rec_title[:200]  # Truncate long titles
            metadata["is_header_chunk"] = True
        else:
            # Look for recommendation number in text (e.g., "in Recommendation 10")
            rec_pattern = r'[Rr]ecommendation\s+(\d+)'
            match = re.search(rec_pattern, chunk_text)
            if match:
                metadata["recommendation_number"] = match.group(1)
                metadata["is_header_chunk"] = False
            else:
                metadata["is_header_chunk"] = False
        
        # Extract key numbers (e.g., "15,000 USD", "15,000 EUR")
        number_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?:\s*(?:USD|EUR|€|$))'
        numbers = re.findall(number_pattern, chunk_text)
        if numbers:
            metadata["key_numbers"] = numbers[:5]  # Store up to 5 key numbers
        
        return metadata
    
    def _ensure_header_in_chunk(self, chunk_text: str, chunk_start: int, sentences_with_offsets: List[Tuple[str, int, int]], full_text: str) -> Tuple[str, bool]:
        """
        Ensure recommendation header is included in chunk.
        
        For legal documents, chunks should start with or include the recommendation header.
        
        Args:
            chunk_text: Original chunk text
            chunk_start: Start character offset
            sentences_with_offsets: All sentences with offsets
            full_text: Full document text
            
        Returns:
            Tuple of (modified_text, was_modified)
        """
        # Check if chunk starts with a recommendation header
        preview = chunk_text[:200] if len(chunk_text) > 200 else chunk_text
        is_boundary, rec_num, _ = self._detect_recommendation_boundary(preview)
        
        if is_boundary:
            return chunk_text, False  # Already has header
        
        # Look backwards for the most recent recommendation header
        search_start = max(0, chunk_start - 500)  # Look back up to 500 chars
        search_text = full_text[search_start:chunk_start]
        
        # Find last recommendation header in the search window
        for match in re.finditer(r'Recommendation\s+(\d+)', search_text, re.IGNORECASE):
            header_end = search_start + match.end()
            if header_end > chunk_start - 500:  # Within 500 chars before chunk
                # Extract from header to chunk
                header_text = full_text[search_start + match.start():chunk_start]
                # Add header to chunk
                modified_text = header_text + "\n\n" + chunk_text
                return modified_text, True
        
        return chunk_text, False
    
    def chunk_document(
        self,
        document_data: Dict[str, Any],
        cached_embeddings: np.ndarray = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document using semantic percentile strategy.
        
        Args:
            document_data: Document dictionary with 'doc_id', 'document_name', and 'pages'
            cached_embeddings: Optional cached embeddings (reused across strategies)
            
        Returns:
            List of chunk dictionaries with metadata
        """
        doc_id = document_data["doc_id"]
        pages = document_data["pages"]
        
        # Extract metadata - ONLY use defaults if missing
        metadata = self._extract_metadata(document_data, doc_id)
        
        logger.info(f"Starting semantic percentile chunking for {doc_id}")
        
        # Build document stream
        full_text, page_map = self._build_document_stream(pages)
        
        # Split into sentences with CORRECT offsets
        sentences_with_offsets = self._split_sentences_with_offsets(full_text)
        
        sentence_count = len(sentences_with_offsets)
        logger.info(f"Document has {sentence_count} sentences")
        
        if sentence_count == 0:
            return []
        
        # Safety: enforce max sentences limit
        if sentence_count > self.MAX_SENTENCES_PER_DOC:
            logger.warning(f"Truncating from {sentence_count} to {self.MAX_SENTENCES_PER_DOC} sentences")
            sentences_with_offsets = sentences_with_offsets[:self.MAX_SENTENCES_PER_DOC]
            sentence_count = self.MAX_SENTENCES_PER_DOC
        
        # Extract just texts for embedding
        sentence_texts = [s[0] for s in sentences_with_offsets]
        
        # Embed all sentences (batched) OR use cached embeddings
        if cached_embeddings is not None:
            logger.info("Using cached embeddings")
            embeddings = cached_embeddings
        else:
            logger.info(f"Embedding {sentence_count} sentences in batches of {self.EMBEDDING_BATCH_SIZE}")
            embeddings = self._embed_texts_batched(sentence_texts)
        
        # Compute similarity between adjacent sentences (O(N), not O(N²))
        similarities = []
        for i in range(sentence_count - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
        
        if len(similarities) == 0:
            # Single sentence - return as one chunk
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "text": full_text,
                "strategy": "semantic_percentile",
                "page_numbers": list(range(1, len(pages) + 1)),
                "char_range": [0, len(full_text)],
                "position": 0,
                **metadata
            }
            logger.info(f"Created 1 chunk (single sentence)")
            return [chunk]
        
        # Compute similarity deltas
        deltas = []
        for i in range(len(similarities) - 1):
            deltas.append(similarities[i] - similarities[i + 1])
        
        # Find percentile threshold
        if len(deltas) > 0:
            threshold = np.percentile(deltas, self.percentile_threshold)
        else:
            threshold = 0.0
        
        logger.info(f"Similarity threshold: {threshold:.4f} (percentile: {self.percentile_threshold})")
        
        # Identify chunk boundaries where similarity drops significantly
        boundaries = [0]  # Always start at 0
        
        for i, delta in enumerate(deltas):
            if delta > threshold:
                boundaries.append(i + 1)
        
        boundaries.append(sentence_count)  # Always end at last sentence
        
        # Create chunks
        chunks = []
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            # Get text for this chunk - NO sentences.index()!
            chunk_sentences = sentences_with_offsets[start_idx:end_idx]
            chunk_text = " ".join([s[0] for s in chunk_sentences])
            
            # Get character range from ORIGINAL offsets (CRITICAL)
            chunk_start = chunk_sentences[0][1]
            chunk_end = chunk_sentences[-1][2]
            
            # Check token count
            token_count = self._estimate_tokens(chunk_text)
            
            # Skip if too small (will be merged)
            if token_count < self.min_tokens:
                continue
            
            # Split if too large
            if token_count > self.max_tokens:
                # Split by sentences into multiple chunks
                current_chunk_sentences = []
                current_tokens = 0
                sent_idx = start_idx
                
                while sent_idx < end_idx:
                    sent_text, sent_start, sent_end = sentences_with_offsets[sent_idx]
                    sent_tokens = self._estimate_tokens(sent_text)
                    
                    if current_tokens + sent_tokens > self.max_tokens and current_chunk_sentences:
                        # Create chunk
                        chunk_text = " ".join([s[0] for s in current_chunk_sentences])
                        chunk_start_char = current_chunk_sentences[0][1]
                        chunk_end_char = current_chunk_sentences[-1][2]
                        
                        chunks.append({
                            "chunk_id": str(uuid.uuid4()),
                            "doc_id": doc_id,
                            "text": chunk_text,
                            "strategy": "semantic_percentile",
                            "page_numbers": self._get_pages_for_chunk(chunk_start_char, chunk_end_char, page_map),
                            "char_range": [chunk_start_char, chunk_end_char],
                            "position": len(chunks),
                            **metadata
                        })
                        
                        current_chunk_sentences = []
                        current_tokens = 0
                    
                    current_chunk_sentences.append(sentences_with_offsets[sent_idx])
                    current_tokens += sent_tokens
                    sent_idx += 1
                
                # Add remaining sentences
                if current_chunk_sentences:
                    chunk_text = " ".join([s[0] for s in current_chunk_sentences])
                    chunk_start_char = current_chunk_sentences[0][1]
                    chunk_end_char = current_chunk_sentences[-1][2]
                    
                    chunks.append({
                        "chunk_id": str(uuid.uuid4()),
                        "doc_id": doc_id,
                        "text": chunk_text,
                        "strategy": "semantic_percentile",
                        "page_numbers": self._get_pages_for_chunk(chunk_start_char, chunk_end_char, page_map),
                        "char_range": [chunk_start_char, chunk_end_char],
                        "position": len(chunks),
                        **metadata
                    })
            else:
                # Ensure header is included in chunk (for legal documents)
                if Config.PRESERVE_HEADERS:
                    chunk_text, was_modified = self._ensure_header_in_chunk(
                        chunk_text, chunk_start, sentences_with_offsets, full_text
                    )
                    if was_modified:
                        # Update char range if header was added
                        chunk_start = max(0, chunk_start - 500)
                
                # Extract recommendation-specific metadata
                rec_metadata = self._extract_recommendation_metadata(
                    chunk_text, chunk_start, sentences_with_offsets
                )
                
                # Create chunk with enhanced metadata
                chunk_dict = {
                    "chunk_id": str(uuid.uuid4()),
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "strategy": "semantic_percentile",
                    "page_numbers": self._get_pages_for_chunk(chunk_start, chunk_end, page_map),
                    "char_range": [chunk_start, chunk_end],
                    "position": len(chunks),
                    **metadata,
                    **rec_metadata  # Add recommendation-specific metadata
                }
                
                # Add token count to metadata
                chunk_dict["chunk_size"] = self._estimate_tokens(chunk_text)
                chunk_dict["total_chunks"] = 0  # Will be updated after all chunks created
                
                chunks.append(chunk_dict)
        
        # Merge chunks that are too small with adjacent chunks
        if len(chunks) > 1:
            merged_chunks = [chunks[0]]
            
            for chunk in chunks[1:]:
                prev_chunk = merged_chunks[-1]
                
                # If previous chunk is too small, merge
                if self._estimate_tokens(prev_chunk["text"]) < self.min_tokens:
                    merged_text = prev_chunk["text"] + " " + chunk["text"]
                    merged_start = prev_chunk["char_range"][0]
                    merged_end = chunk["char_range"][1]
                    
                    merged_chunk = {
                        "chunk_id": prev_chunk["chunk_id"],
                        "doc_id": doc_id,
                        "text": merged_text,
                        "strategy": "semantic_percentile",
                        "page_numbers": sorted(list(set(prev_chunk["page_numbers"] + chunk["page_numbers"]))),
                        "char_range": [merged_start, merged_end],
                        "position": prev_chunk["position"],
                        **metadata
                    }
                    
                    merged_chunks[-1] = merged_chunk
                else:
                    merged_chunks.append(chunk)
            
            chunks = merged_chunks
        
        # Safety: enforce max chunks limit
        if len(chunks) > self.MAX_CHUNKS_PER_DOC:
            logger.warning(f"Truncating from {len(chunks)} to {self.MAX_CHUNKS_PER_DOC} chunks")
            chunks = chunks[:self.MAX_CHUNKS_PER_DOC]
        
        # Update positions
        for i, chunk in enumerate(chunks):
            chunk["position"] = i
        
        logger.info(f"Created {len(chunks)} chunks (semantic percentile)")
        return chunks