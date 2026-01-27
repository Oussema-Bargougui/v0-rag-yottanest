#!/usr/bin/env python3
"""
LLM Answer Module for RAG Pipeline

This module provides LLM-based answer generation for the RAG pipeline,
using local Ollama with Llama 3.1 to generate answers based on retrieved context.

Key Features:
- Integration with local Ollama server
- Context-aware answer generation
- Source citation in responses
- Professional formatting for AML/KYC compliance context
- Error handling and fallback responses

Typical Usage:
    >>> from modules.llm_answer import LLMAnswerGenerator
    >>> generator = LLMAnswerGenerator()
    >>> answer = generator.generate_answer(query, retrieved_chunks)
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMAnswerGenerator:
    """
    A class for generating answers using local LLM (Ollama with Llama 3.1).

    This class provides methods to generate contextual answers based on
    retrieved document chunks, with source citations and professional formatting.

    Attributes:
        base_url (str): Ollama API base URL
        model (str): Model name to use
        timeout (int): Request timeout in seconds
    """

    def __init__(self,
                 base_url: str = "http://localhost:11434",
                 model: str = "llama3.1:latest",
                 timeout: int = 120):
        """
        Initialize the LLMAnswerGenerator.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.1:latest)
            timeout: Request timeout in seconds (default: 120)
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()

        logger.info(f"LLMAnswerGenerator initialized with model: {model}")

    def check_connection(self) -> bool:
        """
        Check if Ollama server is running and accessible.

        Returns:
            True if connected, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string for the LLM.

        Args:
            chunks: List of retrieved document chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documents found."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '')
            filename = chunk.get('filename', 'Unknown')
            score = chunk.get('similarity_score', 0)

            # Include source information
            context_parts.append(f"[Source {i}: {filename} (relevance: {score:.2f})]")
            context_parts.append(text)
            context_parts.append("")  # Empty line between chunks

        return "\n".join(context_parts)

    def _create_prompt(self,
                       query: str,
                       context: str,
                       system_prompt: Optional[str] = None) -> str:
        """
        Create the full prompt for the LLM.

        Args:
            query: User's question
            context: Formatted context from retrieved chunks
            system_prompt: Optional custom system prompt

        Returns:
            Complete prompt string
        """
        if system_prompt is None:
            system_prompt = """You are an intelligent document assistant for Yottanest, an AML/KYC compliance platform. Your role is to help compliance analysts understand documents related to banking regulations, customer due diligence, and financial compliance.

GUIDELINES:
1. Answer questions based ONLY on the provided context documents
2. If the context doesn't contain relevant information, clearly state that
3. Always cite your sources by referring to the document names
4. Be precise and professional in your responses
5. If you're unsure about something, acknowledge the uncertainty
6. Format your response clearly with sections if needed
7. Focus on actionable insights for compliance professionals"""

        prompt = f"""{system_prompt}

CONTEXT DOCUMENTS:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
Based on the context documents above, provide a clear and comprehensive answer to the user's question. Include relevant citations to the source documents. If the documents don't contain enough information to fully answer the question, clearly state what information is available and what is missing.

ANSWER:"""

        return prompt

    def generate_answer(self,
                        query: str,
                        chunks: List[Dict[str, Any]],
                        system_prompt: Optional[str] = None,
                        max_tokens: int = 1500,
                        temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate an answer based on the query and retrieved chunks.

        Args:
            query: User's question
            chunks: List of retrieved document chunks
            system_prompt: Optional custom system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            # Format context from chunks
            context = self._format_context(chunks)

            # Create full prompt
            prompt = self._create_prompt(query, context, system_prompt)

            # Call Ollama API
            logger.info(f"Generating answer for query: {query[:50]}...")

            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            answer_text = result.get("response", "").strip()

            # Extract source information
            sources = []
            for chunk in chunks:
                source = {
                    "filename": chunk.get("filename", "Unknown"),
                    "chunk_id": chunk.get("chunk_id", 0),
                    "similarity_score": chunk.get("similarity_score", 0),
                    "text_preview": chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
                }
                sources.append(source)

            return {
                "success": True,
                "answer": answer_text,
                "sources": sources,
                "query": query,
                "model": self.model,
                "chunks_used": len(chunks),
                "generated_at": datetime.now().isoformat(),
                "error": None
            }

        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama. Please ensure Ollama is running (ollama serve)."
            logger.error(error_msg)
            return self._create_error_response(query, chunks, error_msg)

        except requests.exceptions.Timeout:
            error_msg = "Request to Ollama timed out. The model may be loading or overloaded."
            logger.error(error_msg)
            return self._create_error_response(query, chunks, error_msg)

        except Exception as e:
            error_msg = f"Error generating answer: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(query, chunks, error_msg)

    def _create_error_response(self,
                               query: str,
                               chunks: List[Dict[str, Any]],
                               error: str) -> Dict[str, Any]:
        """
        Create an error response with fallback information.

        Args:
            query: Original query
            chunks: Retrieved chunks
            error: Error message

        Returns:
            Error response dictionary
        """
        # Provide a fallback response with just the context
        fallback_answer = "I was unable to generate an AI-powered response. Here are the relevant document excerpts:\n\n"

        for i, chunk in enumerate(chunks[:3], 1):
            fallback_answer += f"**Source {i}: {chunk.get('filename', 'Unknown')}**\n"
            fallback_answer += chunk.get('text', '')[:500] + "...\n\n"

        sources = [
            {
                "filename": chunk.get("filename", "Unknown"),
                "chunk_id": chunk.get("chunk_id", 0),
                "similarity_score": chunk.get("similarity_score", 0),
                "text_preview": chunk.get("text", "")[:200] + "..."
            }
            for chunk in chunks
        ]

        return {
            "success": False,
            "answer": fallback_answer,
            "sources": sources,
            "query": query,
            "model": self.model,
            "chunks_used": len(chunks),
            "generated_at": datetime.now().isoformat(),
            "error": error
        }

    def generate_streaming_answer(self,
                                  query: str,
                                  chunks: List[Dict[str, Any]],
                                  system_prompt: Optional[str] = None,
                                  max_tokens: int = 1500,
                                  temperature: float = 0.7):
        """
        Generate an answer with streaming response.

        Args:
            query: User's question
            chunks: List of retrieved document chunks
            system_prompt: Optional custom system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Yields:
            Chunks of the response as they're generated
        """
        try:
            # Format context from chunks
            context = self._format_context(chunks)

            # Create full prompt
            prompt = self._create_prompt(query, context, system_prompt)

            # Call Ollama API with streaming
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                },
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            # Stream the response
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {str(e)}"


def main():
    """Example usage of the LLMAnswerGenerator."""
    generator = LLMAnswerGenerator()

    # Check connection
    if generator.check_connection():
        print("Connected to Ollama!")

        # Example query
        query = "What are the key compliance requirements?"

        # Example chunks (would normally come from retriever)
        chunks = [
            {
                "text": "Banks must implement KYC procedures to verify customer identity...",
                "filename": "compliance_guide.pdf",
                "chunk_id": 1,
                "similarity_score": 0.85
            },
            {
                "text": "AML regulations require monitoring of suspicious transactions...",
                "filename": "aml_policy.pdf",
                "chunk_id": 2,
                "similarity_score": 0.78
            }
        ]

        # Generate answer
        result = generator.generate_answer(query, chunks)

        print(f"\nQuery: {query}")
        print(f"\nAnswer: {result['answer']}")
        print(f"\nSources used: {len(result['sources'])}")
    else:
        print("Could not connect to Ollama. Please ensure it's running.")


if __name__ == "__main__":
    main()
