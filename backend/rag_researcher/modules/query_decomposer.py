"""
Query Decomposer Module

Uses LLM to intelligently decompose complex queries into sub-questions.

Responsibilities:
- Detect sub-questions in complex queries
- Handle typos, missing punctuation, natural language
- Return JSON-structured decomposition
- Support single-query and multi-query scenarios

Author: Yottanest Team
Version: 1.0.0 - LLM-Based Decomposition
"""

import logging
import json
import httpx
from typing import List, Dict, Any
import sys
from pathlib import Path

# Fix import when running module directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """Decomposes queries using LLM (gpt-3.5-turbo)."""
    
    def __init__(self, model: str = None):
        """
        Initialize query decomposer.
        
        Args:
            model: OpenRouter model name (uses Config.DECOMPOSITION_MODEL if None)
        """
        self.model = model if model else Config.DECOMPOSITION_MODEL
        self.api_key = Config.OPENROUTER_API_KEY
        self.base_url = Config.OPENROUTER_BASE_URL
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        logger.info(f"Query decomposer initialized with model: {self.model}")
    
    SYSTEM_PROMPT = """You are a query decomposition expert. Your task is to analyze user queries and identify distinct sub-questions or topics.

## Rules:
1. Split complex queries into distinct sub-questions when multiple questions or topics are present
2. Handle typos, missing punctuation, and natural language gracefully
3. Each sub-question should be self-contained and answerable
4. If the query contains only one question/topic, return it as a single sub-question
5. Return JSON only - no explanations outside JSON

## Output Format:
{
  "sub_queries": [
    {
      "id": 0,
      "question": "Complete, standalone, grammatically correct question",
      "original_text": "Text from original query (may have typos, no punctuation)"
    }
  ]
}

## Examples:

Example 1 - Multi-query with "and":
Input: "According to FATF Recommendations explain RBA impact on CDD, and using Pollen Street report explain how PE and PC contribute to resilience"

Output:
{
  "sub_queries": [
    {
      "id": 0,
      "question": "According to FATF Recommendations, explain the impact of Risk-Based Approach (RBA) on Customer Due Diligence (CDD)",
      "original_text": "According to FATF Recommendations explain RBA impact on CDD"
    },
    {
      "id": 1,
      "question": "Using the Pollen Street report, explain how Private Equity (PE) and Private Credit (PC) contribute to resilience",
      "original_text": "using Pollen Street report explain how PE and PC contribute to resilience"
    }
  ]
}

Example 2 - No punctuation, implicit multiple topics:
Input: "FATF RBA requirements Pollen Street risk management"

Output:
{
  "sub_queries": [
    {
      "id": 0,
      "question": "What are the FATF Risk-Based Approach (RBA) requirements?",
      "original_text": "FATF RBA requirements"
    },
    {
      "id": 1,
      "question": "What is the risk management strategy according to the Pollen Street report?",
      "original_text": "Pollen Street risk management"
    }
  ]
}

Example 3 - Single query with typos:
Input: "Wat is CDD in FATF?"

Output:
{
  "sub_queries": [
    {
      "id": 0,
      "question": "What is Customer Due Diligence (CDD) in the FATF recommendations?",
      "original_text": "Wat is CDD in FATF?"
    }
  ]
}

Example 4 - Single query, comma-separated topics but actually one question:
Input: "Explain the Risk-Based Approach requirements in FATF"

Output:
{
  "sub_queries": [
    {
      "id": 0,
      "question": "Explain the Risk-Based Approach requirements in FATF recommendations",
      "original_text": "Explain the Risk-Based Approach requirements in FATF"
    }
  ]
}"""
    
    def decompose(self, query: str) -> List[Dict[str, Any]]:
        """
        Decompose query using LLM.
        
        Args:
            query: User's query string
            
        Returns:
            List of sub-queries with metadata:
            [
              {
                "id": int,
                "question": str (cleaned, grammatically correct),
                "original_text": str (from input query)
              }
            ]
            
        Raises:
            ValueError: If decomposition fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.info(f"Decomposing query: '{query[:100]}...'")
        
        try:
            # Call LLM for decomposition
            sub_queries = self._call_llm(query)
            
            logger.info(f"Decomposed into {len(sub_queries)} sub-queries")
            
            # Validate structure
            if not sub_queries or not isinstance(sub_queries, list):
                raise ValueError("Invalid decomposition result")
            
            # Validate each sub-query
            for sq in sub_queries:
                if "id" not in sq or "question" not in sq:
                    raise ValueError(f"Invalid sub-query structure: {sq}")
            
            return sub_queries
            
        except Exception as e:
            logger.error(f"Query decomposition failed: {str(e)}")
            # Fallback: return single sub-query with original query
            logger.warning("Falling back to single-query decomposition")
            return [
                {
                    "id": 0,
                    "question": query.strip(),
                    "original_text": query.strip()
                }
            ]
    
    def _call_llm(self, query: str) -> List[Dict[str, Any]]:
        """
        Call LLM API for query decomposition.
        
        Args:
            query: User query string
            
        Returns:
            List of sub-queries
            
        Raises:
            Exception: On API failure or invalid response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yottanest.com",
            "X-Title": "Yottanest RAG"
        }
        
        user_prompt = f"""Analyze this user query and decompose it into distinct sub-questions if multiple questions/topics are present:

Query: {query}

Return JSON only."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,  # Deterministic output
            "max_tokens": 1000
        }
        
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise ValueError("Invalid API response structure")
            
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON response
            # Clean response - remove markdown code blocks if present
            cleaned_content = content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            result = json.loads(cleaned_content)
            
            if "sub_queries" not in result:
                raise ValueError("Missing 'sub_queries' in decomposition result")
            
            return result["sub_queries"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Decomposition API failed: {e.response.status_code}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decomposition JSON: {str(e)}")
            logger.debug(f"Raw content: {content[:500]}...")
            raise Exception(f"Invalid JSON from decomposition: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in decomposition: {str(e)}", exc_info=True)
            raise


# =============================================================================
# Test Method (Manual Verification)
# =============================================================================

if __name__ == "__main__":
    """
    Test query decomposer with sample queries.
    
    Usage:
        python modules/query_decomposer.py
    """
    logging.basicConfig(level=logging.INFO)
    
    decomposer = QueryDecomposer()
    
    # Test cases
    test_queries = [
        "According to FATF Recommendations explain RBA impact on CDD, and using Pollen Street report explain how PE and PC contribute to resilience",
        "What is CDD?",
        "FATF RBA requirements Pollen Street risk management",
        "Wat is CDD in FATF?",  # Typo
        "Explain the Risk-Based Approach requirements in FATF",
        "CDD, record keeping, and ongoing monitoring",  # Multiple questions
    ]
    
    print("\n=== Query Decomposition Tests ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 60)
        
        try:
            sub_queries = decomposer.decompose(query)
            
            print(f"Decomposed into {len(sub_queries)} sub-query(ies):")
            for sq in sub_queries:
                print(f"\n  ID: {sq['id']}")
                print(f"  Question: {sq['question']}")
                print(f"  Original: {sq['original_text']}")
        
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()