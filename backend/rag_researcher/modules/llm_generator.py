"""
LLM Generator Module (Orchestrator)

Coordinates all generation components to produce grounded answers.

Responsibilities:
- Orchestrate context building, prompting, generation, and formatting
- Handle errors gracefully
- Provide clean interface for RAG queries
- Log comprehensive metrics
- Support multi-query scenarios with automatic decomposition

Author: Yottanest Team
Version: 2.0.0 - Multi-Query Support
"""
import logging
from typing import List, Dict, Optional
from .context_builder import ContextBuilder
from .prompt_builder import PromptBuilder
from .llm_client import LLMClient
from .answer_formatter import AnswerFormatter
from .query_decomposer import QueryDecomposer
from .retriever import Retriever

logger = logging.getLogger(__name__)


class LLMGenerator:
    """Orchestrates LLM generation for RAG queries."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        context_builder: Optional[ContextBuilder] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        answer_formatter: Optional[AnswerFormatter] = None,
        retriever: Optional[Retriever] = None
    ):
        """
        Initialize LLM generator with all components.
        
        Args:
            llm_client: Optional LLM client instance
            context_builder: Optional context builder instance
            prompt_builder: Optional prompt builder instance
            answer_formatter: Optional answer formatter instance
            retriever: Optional retriever instance for multi-query support
        """
        self.llm_client = llm_client or LLMClient()
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.answer_formatter = answer_formatter or AnswerFormatter()
        self.retriever = retriever
        
        logger.info("LLM generator initialized")
    
    def generate(
        self,
        query: str,
        chunks: List[Dict],
        max_context_tokens: Optional[int] = None
    ) -> Dict:
        """
        Generate answer for query using retrieved chunks.
        
        Args:
            query: User's question
            chunks: List of retrieved chunks from retriever
            max_context_tokens: Optional override for max context tokens
            
        Returns:
            Structured answer dictionary
            
        Raises:
            ValueError: If query is empty
            RuntimeError: If generation fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not chunks:
            logger.warning("No chunks provided for generation")
            return self._handle_no_chunks(query)
        
        logger.info(f"Starting generation for query: '{query[:50]}...'")
        logger.info(f"Retrieved {len(chunks)} chunks")
        
        try:
            # Step 1: Build context from chunks
            logger.debug("Step 1: Building context")
            context = self.context_builder.build(
                chunks,
                max_tokens=max_context_tokens
            )
            
            if not context:
                logger.warning("Context is empty after building")
                return self._handle_no_context(query)
            
            # Validate context
            if not self.context_builder.validate_context(context):
                logger.error("Context validation failed")
                return self.answer_formatter.format_error(
                    "Context validation failed",
                    context,
                    self.llm_client.model
                )
            
            # Step 2: Build prompts
            logger.debug("Step 2: Building prompts")
            prompts = self.prompt_builder.build(query, context)
            
            # Validate prompts
            if not self.prompt_builder.validate_prompt(prompts):
                logger.error("Prompt validation failed")
                return self.answer_formatter.format_error(
                    "Prompt validation failed",
                    context,
                    self.llm_client.model
                )
            
            # Step 3: Generate answer using LLM
            logger.debug("Step 3: Generating answer with LLM")
            raw_response = self.llm_client.generate(
                prompt=prompts["user"],
                system_prompt=prompts["system"]
            )
            
            if not raw_response:
                logger.warning("LLM returned empty response")
                return self._handle_empty_response(query, context)
            
            # Step 4: Format and validate answer
            logger.debug("Step 4: Formatting answer")
            answer = self.answer_formatter.format(
                raw_response=raw_response,
                context=context,
                model=self.llm_client.model
            )
            
            # Add query to response
            answer["query"] = query
            
            logger.info(f"Generated answer with confidence: {answer['confidence']}")
            logger.info(f"Used {len(context)} chunks, {len(answer['citations'])} citations")
            
            return answer
            
        except ValueError as e:
            logger.error(f"Value error in generation: {str(e)}")
            return self.answer_formatter.format_error(
                f"Invalid input: {str(e)}",
                chunks,
                self.llm_client.model
            )
        except RuntimeError as e:
            logger.error(f"Runtime error in generation: {str(e)}")
            return self.answer_formatter.format_error(
                f"Generation failed: {str(e)}",
                chunks,
                self.llm_client.model
            )
        except Exception as e:
            logger.error(f"Unexpected error in generation: {str(e)}", exc_info=True)
            return self.answer_formatter.format_error(
                f"Unexpected error: {str(e)}",
                chunks,
                self.llm_client.model
            )
    
    def _handle_no_chunks(self, query: str) -> Dict:
        """Handle case when no chunks are available."""
        error_msg = "No relevant documents found in knowledge base. Cannot answer query without context."
        logger.warning(f"No chunks for query: '{query}'")
        
        return {
            "answer": error_msg,
            "evidence": "",
            "limitations": "No relevant documents were found for this query.",
            "citations": [],
            "chunks_used": [],
            "chunks_count": 0,
            "citation_validation": {
                "total_citations": 0,
                "valid_citations": 0,
                "invalid_citations": 0,
                "valid_chunk_ids": [],
                "invalid_chunk_ids": [],
                "validation_rate": 1.0
            },
            "confidence": "low",
            "model": self.llm_client.model,
            "timestamp": "",
            "query": query,
            "error": "no_chunks"
        }
    
    def _handle_no_context(self, query: str) -> Dict:
        """Handle case when context building fails."""
        error_msg = "Context could not be built from retrieved chunks."
        logger.error(f"Context building failed for query: '{query}'")
        
        return self.answer_formatter.format_error(
            error_msg,
            [],
            self.llm_client.model
        )
    
    def _handle_empty_response(self, query: str, context: List[Dict]) -> Dict:
        """Handle case when LLM returns empty response."""
        error_msg = "LLM returned empty response. Please try again."
        logger.warning(f"Empty LLM response for query: '{query}'")
        
        answer = self.answer_formatter.format_error(
            error_msg,
            context,
            self.llm_client.model
        )
        answer["query"] = query
        
        return answer
    
    def check_components(self) -> Dict[str, bool]:
        """Check if all components are working."""
        status = {}
        
        try:
            status["llm_client"] = self.llm_client.check_connection()
        except Exception as e:
            logger.error(f"LLM client check failed: {str(e)}")
            status["llm_client"] = False
        
        status["context_builder"] = True
        status["prompt_builder"] = True
        status["answer_formatter"] = True
        
        return status
    
    def generate_smart(
        self,
        query: str,
        session_id: Optional[str] = None,
        enable_decomposition: bool = True
    ) -> Dict:
        """
        Smart generation with automatic query decomposition.
        
        Workflow:
        1. Try LLM decomposition (if enabled)
        2. If fails -> fall back to single-query path
        3. If succeeds with 1 sub-query -> same as current generate()
        4. If succeeds with >1 sub-queries -> use multi-query path
        
        Ensures backward compatibility always works.
        
        Args:
            query: User's question
            session_id: Optional session ID for retrieval
            enable_decomposition: Enable/disable decomposition (default: True)
            
        Returns:
            Structured answer dictionary
            
        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.info(f"Starting smart generation for query: '{query[:50]}...'")
        
        # Initialize retriever if not available
        if self.retriever is None:
            logger.warning("No retriever provided, using single-query path only")
            enable_decomposition = False
        
        if not enable_decomposition or self.retriever is None:
            # Use existing single-query path (backward compatible)
            logger.info("Using single-query path (decomposition disabled)")
            return self._generate_single_query(query, session_id)
        
        try:
            # Step 1: Decompose query
            logger.info("Step 1: Decomposing query using LLM")
            decomposer = QueryDecomposer()
            sub_queries = decomposer.decompose(query)
            
            logger.info(f"Decomposed into {len(sub_queries)} sub-queries")
            
            # Step 2: Check if single or multi
            if len(sub_queries) == 1:
                # Single sub-query: use existing path (backward compatible)
                logger.info("Single query detected, using standard path")
                return self._generate_single_query(query, session_id)
            else:
                # Multi-sub-query: use new multi-query path
                logger.info(f"Multi-query detected ({len(sub_queries)} sub-questions)")
                return self._generate_multi_query(query, session_id, sub_queries)
        
        except Exception as e:
            # Fallback to single-query on any error
            logger.warning(f"Decomposition failed, falling back to single-query: {str(e)}")
            return self._generate_single_query(query, session_id)
    
    def _generate_single_query(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Generate answer using single-query path (existing logic).
        
        Backward compatible - uses existing generate() method.
        
        Args:
            query: User's question
            session_id: Optional session ID
            
        Returns:
            Structured answer dictionary
        """
        logger.info("Using single-query generation path")
        
        # Retrieve chunks
        chunks = self.retriever.retrieve(query, session_id=session_id)
        
        if not chunks:
            logger.warning("No chunks retrieved")
            return self._handle_no_chunks(query)
        
        # Use existing generate() method
        return self.generate(query, chunks)
    
    def _generate_multi_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        sub_queries: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate answer using multi-query path.
        
        Args:
            query: Original user query
            session_id: Optional session ID
            sub_queries: List of sub-queries from decomposer
            
        Returns:
            Structured answer dictionary with multi-query format
        """
        logger.info(f"Using multi-query generation path ({len(sub_queries)} sub-queries)")
        
        try:
            # Step 1: Retrieve for each sub-query
            logger.info("Step 1: Retrieving for each sub-query")
            results_by_query = self.retriever.retrieve_multi_query(
                sub_queries,
                session_id=session_id
            )
            
            # Step 2: Build context with diversity
            logger.info("Step 2: Building context with smart diversity")
            context = self.context_builder.build_multi_query_context(results_by_query)
            
            if not context:
                logger.warning("Context is empty after building")
                return self._handle_no_chunks(query)
            
            # Step 3: Build prompts with sub-query instructions
            logger.info("Step 3: Building multi-query prompts")
            user_prompt = self.prompt_builder.build_user_prompt_multi_query(
                query=query,
                context=context,
                sub_queries=sub_queries
            )
            system_prompt = self.prompt_builder.build_system_prompt()
            
            # Step 4: Generate answer
            logger.info("Step 4: Generating multi-query answer")
            raw_response = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            if not raw_response:
                logger.warning("LLM returned empty response")
                return self._handle_empty_response(query, context)
            
            # Step 5: Format answer
            logger.info("Step 5: Formatting multi-query answer")
            answer = self.answer_formatter.format(
                raw_response=raw_response,
                context=context,
                model=self.llm_client.model
            )
            
            # Add metadata
            answer["query"] = query
            answer["sub_queries"] = sub_queries
            answer["is_multi_query"] = True
            
            logger.info(f"Generated multi-query answer with confidence: {answer['confidence']}")
            
            return answer
            
        except Exception as e:
            logger.error(f"Multi-query generation failed: {str(e)}", exc_info=True)
            # Fallback to single-query
            logger.warning("Falling back to single-query path")
            return self._generate_single_query(query, session_id)