"""
Answer Formatter Module

Formats raw LLM output into structured answer with validation.

Responsibilities:
- Parse JSON responses from LLM
- Extract structured sections (answer, reasoning, implications, limitations)
- Validate citations against context
- Return structured answer

Author: Yottanest Team
Version: 2.0.0 - JSON Response Parser
"""
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AnswerFormatter:
    """Formats LLM JSON output into structured answers."""
    
    # JSON keys expected in LLM response
    REQUIRED_KEYS = ["answer", "reasoning", "implications", "limitations", "citations", "confidence"]
    
    def __init__(self):
        """Initialize answer formatter."""
        logger.info("Answer formatter initialized (JSON parser mode)")
    
    def format(
        self,
        raw_response: str,
        context: List[Dict],
        model: str = "gpt-4o-mini"
    ) -> Dict:
        """
        Format raw LLM JSON response into structured answer.
        
        Args:
            raw_response: Raw JSON text from LLM
            context: List of context items used for generation
            model: Model name used for generation
            
        Returns:
            Structured answer dictionary
            
        Raises:
            ValueError: If raw_response is empty or invalid JSON
        """
        if not raw_response or not raw_response.strip():
            raise ValueError("Raw response cannot be empty")
        
        logger.info(f"Formatting JSON response from model: {model}")
        logger.debug(f"Raw response length: {len(raw_response)} chars")
        
        # Parse JSON response
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = raw_response.strip()
            
            # Remove ```json and ``` if present
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            parsed_response = json.loads(cleaned_response)
            
            # Validate required keys
            missing_keys = [k for k in self.REQUIRED_KEYS if k not in parsed_response]
            if missing_keys:
                logger.warning(f"Missing required keys in JSON: {missing_keys}")
                # Add missing keys with defaults
                for key in missing_keys:
                    if key == "citations":
                        parsed_response[key] = []
                    elif key == "confidence":
                        parsed_response[key] = "low"
                    else:
                        parsed_response[key] = ""
            
            # Extract fields
            answer_text = parsed_response.get("answer", "")
            reasoning = parsed_response.get("reasoning", "")
            implications = parsed_response.get("implications", "")
            limitations = parsed_response.get("limitations", "")
            citations = parsed_response.get("citations", [])
            confidence = parsed_response.get("confidence", "low")
            
            # Validate citations against context
            validation_result = self._validate_citations(citations, context)
            
            # Override confidence if citations invalid
            if validation_result["invalid_citations"] > 0:
                confidence = "low"
                logger.warning("Invalid citations detected - setting confidence to low")
            
            # Build chunks_used list
            chunks_used = [item["chunk_id"] for item in context]
            
            # Build structured response
            answer = {
                "answer": answer_text,
                "reasoning": reasoning,
                "implications": implications,
                "limitations": limitations,
                "citations": citations,
                "chunks_used": chunks_used,
                "chunks_count": len(chunks_used),
                "citation_validation": validation_result,
                "confidence": confidence,
                "model": model,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "raw_response": raw_response
            }
            
            logger.info(f"Formatted JSON answer with {len(citations)} citations, confidence: {confidence}")
            
            return answer
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Raw response: {raw_response[:500]}...")
            
            # Return error with raw response
            return self.format_error(
                f"Failed to parse LLM response as JSON. Raw response: {raw_response[:200]}...",
                context,
                model
            )
        except Exception as e:
            logger.error(f"Unexpected error formatting response: {str(e)}", exc_info=True)
            return self.format_error(
                f"Error formatting response: {str(e)}",
                context,
                model
            )
    
    def _validate_citations(
        self,
        citations: List[str],
        context: List[Dict]
    ) -> Dict:
        """
        Validate citations against context chunks.
        
        Args:
            citations: List of chunk IDs cited by LLM
            context: List of context items used
            
        Returns:
            Validation result dictionary
        """
        # Build set of valid chunk IDs from context
        valid_chunk_ids = {item["chunk_id"] for item in context}
        
        # Validate each citation
        valid_citations = []
        invalid_citations = []
        
        for chunk_id in citations:
            if chunk_id in valid_chunk_ids:
                valid_citations.append(chunk_id)
            else:
                invalid_citations.append(chunk_id)
                logger.warning(f"Invalid citation: {chunk_id} not in context")
        
        # Calculate validation metrics
        validation_result = {
            "total_citations": len(citations),
            "valid_citations": len(valid_citations),
            "invalid_citations": len(invalid_citations),
            "valid_chunk_ids": valid_citations,
            "invalid_chunk_ids": invalid_citations,
            "validation_rate": len(valid_citations) / len(citations) if citations else 1.0
        }
        
        return validation_result
    
    def format_error(
        self,
        error_message: str,
        context: List[Dict],
        model: str = "gpt-4o-mini"
    ) -> Dict:
        """
        Format error response with JSON structure.
        
        Args:
            error_message: Error description
            context: List of context items (may be empty)
            model: Model name
            
        Returns:
            Structured error response
        """
        answer = {
            "answer": f"Error: {error_message}",
            "reasoning": f"An error occurred during generation: {error_message}",
            "implications": "Unable to provide implications due to error.",
            "limitations": f"Error prevented analysis: {error_message}",
            "citations": [],
            "chunks_used": [item["chunk_id"] for item in context],
            "chunks_count": len(context),
            "citation_validation": {
                "total_citations": 0,
                "valid_citations": 0,
                "invalid_citations": 0,
                "valid_chunk_ids": [],
                "invalid_chunk_ids": [],
                "validation_rate": 1.0
            },
            "confidence": "low",
            "model": model,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_message
        }
        
        logger.error(f"Formatted error response: {error_message}")
        
        return answer