#!/usr/bin/env python3
"""
RAG Service Module for Document Processing and Q&A

This module provides a service layer for the RAG pipeline, managing:
- In-memory session storage
- Document upload and processing
- Pipeline orchestration
- Query handling with LLM answers

Integrates with the rag_researcher modules for document processing.

Author: Yottanest Team
Version: 1.0.0
"""

import os
import sys
import uuid
import shutil
import logging
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from enum import Enum

# Add rag_researcher to path for imports
SCRIPT_DIR = Path(__file__).parent.absolute()
RAG_RESEARCHER_DIR = SCRIPT_DIR.parent / "rag_researcher"
sys.path.insert(0, str(RAG_RESEARCHER_DIR))

# Import RAG pipeline modules
from modules.data_loader import DataLoader
from modules.pdf_extractor import process_pdf
from modules.text_cleaner import TextCleaner
from modules.chunker import TextChunker
from modules.embedder import TextEmbedder
from modules.vector_store import VectorStore
from modules.retriever import Retriever
from modules.llm_answer import LLMAnswerGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProcessingStage(str, Enum):
    """Enum for processing pipeline stages."""
    IDLE = "idle"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    READY = "ready"
    ERROR = "error"


class RAGSession:
    """
    Represents a single RAG processing session.

    Stores all state related to a user's document processing session,
    including uploaded files, processing status, and vector store.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Processing state
        self.stage = ProcessingStage.IDLE
        self.progress = 0  # 0-100
        self.stage_message = ""
        self.error_message = None

        # Document storage
        self.temp_dir = SCRIPT_DIR / "temp" / session_id
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.uploaded_files: List[Dict[str, Any]] = []
        self.processed_documents: List[Dict[str, Any]] = []

        # RAG components (initialized during processing)
        self.vector_store: Optional[VectorStore] = None
        self.embedder: Optional[TextEmbedder] = None
        self.retriever: Optional[Retriever] = None

        # Chat history
        self.chat_history: List[Dict[str, Any]] = []

    def update_stage(self, stage: ProcessingStage, progress: int, message: str = ""):
        """Update the processing stage."""
        self.stage = stage
        self.progress = progress
        self.stage_message = message
        self.updated_at = datetime.now()
        logger.info(f"Session {self.session_id}: {stage.value} - {progress}% - {message}")

    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp dir for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {self.session_id}: {e}")


class RAGService:
    """
    Service class for managing RAG sessions and processing.

    Provides methods for:
    - Creating and managing sessions
    - Uploading documents
    - Processing documents through the RAG pipeline
    - Querying processed documents
    """

    def __init__(self):
        """Initialize the RAG service."""
        self.sessions: Dict[str, RAGSession] = {}
        self._lock = threading.Lock()

        # Initialize shared components
        self.data_loader = DataLoader()
        self.text_cleaner = TextCleaner()
        self.chunker = TextChunker(
            chunk_size=1000,
            overlap_size=200,
            chunking_method="paragraph"
        )
        self.llm_generator = LLMAnswerGenerator()

        logger.info("RAGService initialized")

    def create_session(self) -> str:
        """
        Create a new RAG session.

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())[:8]

        with self._lock:
            session = RAGSession(session_id)
            self.sessions[session_id] = session

        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[RAGSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            RAGSession or None if not found
        """
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and clean up its resources.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            session = self.sessions.pop(session_id, None)

        if session:
            session.cleanup()
            logger.info(f"Deleted session: {session_id}")
            return True

        return False

    def save_uploaded_file(self,
                           session_id: str,
                           filename: str,
                           content: bytes) -> Dict[str, Any]:
        """
        Save an uploaded file to the session's temp directory.

        Args:
            session_id: Session ID
            filename: Original filename
            content: File content as bytes

        Returns:
            File info dictionary
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Save file to temp directory
        file_path = session.temp_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)

        file_info = {
            "filename": filename,
            "path": str(file_path),
            "size": len(content),
            "uploaded_at": datetime.now().isoformat()
        }

        session.uploaded_files.append(file_info)
        session.update_stage(ProcessingStage.UPLOADING, 0, f"Uploaded {filename}")

        logger.info(f"Saved file {filename} for session {session_id}")
        return file_info

    def get_processing_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current processing status for a session.

        Args:
            session_id: Session ID

        Returns:
            Status dictionary
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "session_id": session_id,
                "found": False,
                "error": "Session not found"
            }

        return {
            "session_id": session_id,
            "found": True,
            "stage": session.stage.value,
            "progress": session.progress,
            "message": session.stage_message,
            "error": session.error_message,
            "files_count": len(session.uploaded_files),
            "documents_processed": len(session.processed_documents),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }

    def process_documents(self, session_id: str) -> Dict[str, Any]:
        """
        Process all uploaded documents through the RAG pipeline.

        This is the main processing function that runs the entire pipeline:
        1. Load documents (extract text from PDFs)
        2. Clean text
        3. Chunk documents
        4. Generate embeddings
        5. Store in vector database

        Args:
            session_id: Session ID

        Returns:
            Processing result dictionary
        """
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if not session.uploaded_files:
            return {"success": False, "error": "No files uploaded"}

        try:
            # Stage 1: Extract text from documents
            session.update_stage(ProcessingStage.EXTRACTING, 10, "Extracting text from documents...")

            documents = []
            for file_info in session.uploaded_files:
                file_path = Path(file_info['path'])
                doc = self.data_loader.load_document(file_path)
                if doc:
                    documents.append(doc)

            if not documents:
                raise ValueError("No documents could be loaded")

            session.update_stage(ProcessingStage.EXTRACTING, 20, f"Extracted text from {len(documents)} documents")

            # Stage 2: Clean text
            session.update_stage(ProcessingStage.CLEANING, 30, "Cleaning and preprocessing text...")

            cleaned_documents = self.text_cleaner.clean_documents(documents)
            session.update_stage(ProcessingStage.CLEANING, 40, "Text cleaning complete")

            # Stage 3: Chunk documents
            session.update_stage(ProcessingStage.CHUNKING, 50, "Splitting documents into chunks...")

            chunked_documents = self.chunker.chunk_documents(cleaned_documents)

            # Flatten chunks for embedding
            all_chunks = []
            for doc in chunked_documents:
                for chunk in doc.get('chunks', []):
                    chunk_doc = {
                        'text': chunk['content'],
                        'filename': doc['filename'],
                        'chunk_id': chunk['chunk_id'],
                        'metadata': {
                            'source': doc['filename'],
                            'chunk_id': chunk['chunk_id'],
                            'size_chars': chunk['size_chars']
                        }
                    }
                    all_chunks.append(chunk_doc)

            session.update_stage(ProcessingStage.CHUNKING, 60, f"Created {len(all_chunks)} chunks")

            # Stage 4: Generate embeddings
            session.update_stage(ProcessingStage.EMBEDDING, 70, "Generating embeddings with Nomic...")

            # Initialize embedder for this session using Ollama's nomic-embed-text
            session.embedder = TextEmbedder(
                model_name="nomic-embed-text:latest",
                embedding_dim=768,  # nomic-embed-text produces 768-dim vectors
                model_provider="ollama"
            )

            embedded_chunks = session.embedder.embed_documents(all_chunks)
            session.update_stage(ProcessingStage.EMBEDDING, 85, f"Generated {len(embedded_chunks)} embeddings")

            # Stage 5: Store in vector database
            session.update_stage(ProcessingStage.STORING, 90, "Building vector store...")

            session.vector_store = VectorStore(distance_metric="cosine")
            session.vector_store.add_documents(embedded_chunks)

            # Initialize retriever
            session.retriever = Retriever(
                vector_store=session.vector_store,
                embedder=session.embedder,
                top_k=5,
                reranking_enabled=False,  # Disable for speed
                hybrid_search_enabled=False  # Disable for speed
            )

            # Mark as ready
            session.processed_documents = chunked_documents
            session.update_stage(ProcessingStage.READY, 100, "Processing complete! Ready to answer questions.")

            return {
                "success": True,
                "session_id": session_id,
                "documents_processed": len(documents),
                "chunks_created": len(all_chunks),
                "embeddings_generated": len(embedded_chunks),
                "message": "Documents processed successfully. You can now ask questions."
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Processing error for session {session_id}: {error_msg}")
            session.update_stage(ProcessingStage.ERROR, 0, "")
            session.error_message = error_msg

            return {
                "success": False,
                "session_id": session_id,
                "error": error_msg
            }

    def query_documents(self,
                        session_id: str,
                        query: str,
                        top_k: int = 5) -> Dict[str, Any]:
        """
        Query the processed documents and generate an answer.

        Args:
            session_id: Session ID
            query: User's question
            top_k: Number of chunks to retrieve

        Returns:
            Answer dictionary with response and sources
        """
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if session.stage != ProcessingStage.READY:
            return {
                "success": False,
                "error": f"Documents not ready. Current stage: {session.stage.value}"
            }

        if not session.retriever:
            return {"success": False, "error": "Retriever not initialized"}

        try:
            # Retrieve relevant chunks
            logger.info(f"Retrieving chunks for query: {query}")
            chunks = session.retriever.retrieve(query, top_k=top_k)

            if not chunks:
                return {
                    "success": True,
                    "answer": "I couldn't find any relevant information in the uploaded documents to answer your question.",
                    "sources": [],
                    "query": query
                }

            # Generate answer using LLM
            result = self.llm_generator.generate_answer(query, chunks)

            # Add to chat history
            chat_entry = {
                "query": query,
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "timestamp": datetime.now().isoformat()
            }
            session.chat_history.append(chat_entry)

            return {
                "success": result.get("success", True),
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "query": query,
                "chunks_used": len(chunks),
                "model": result.get("model", "llama3.1"),
                "error": result.get("error")
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query error for session {session_id}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "query": query
            }

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the chat history for a session.

        Args:
            session_id: Session ID

        Returns:
            List of chat entries
        """
        session = self.get_session(session_id)
        if not session:
            return []

        return session.chat_history

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a session.

        Args:
            session_id: Session ID

        Returns:
            Session info dictionary
        """
        session = self.get_session(session_id)
        if not session:
            return {"found": False, "error": "Session not found"}

        return {
            "found": True,
            "session_id": session_id,
            "stage": session.stage.value,
            "progress": session.progress,
            "message": session.stage_message,
            "error": session.error_message,
            "files": session.uploaded_files,
            "documents_processed": len(session.processed_documents),
            "chat_history_count": len(session.chat_history),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }


# Global service instance
rag_service = RAGService()


def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    return rag_service
