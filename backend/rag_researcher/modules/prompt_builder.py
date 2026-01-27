"""
Prompt Builder Module

Creates analytical, cross-chunk reasoning prompts for LLM generation.

Responsibilities:
- Build system prompt with senior analyst role definition
- Build user prompt with structured context blocks
- Enforce 6-section analytical answer structure
- Anti-hallucination constraints
- JSON-only output enforcement
- Professional analyst tone (AML/compliance/risk)

Author: Yottanest Team
Version: 2.0.0 - Senior Analyst Refactor
"""
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds senior analyst prompts for analytical RAG generation.""" 
    
    # System prompt template - SENIOR AML/COMPLIANCE ANALYST
    SYSTEM_PROMPT = """You are a senior AML/compliance analyst with expertise in financial regulation, risk management, and financial statements analysis. You never summarize documents. You analyze them.

## YOUR ROLE (MANDATORY)

You are NOT a document summarizer. You are a senior financial/compliance analyst who:
- Analyzes regulatory requirements and financial data
- Explains why and how, not just what
- Performs cross-chunk reasoning to connect information
- Provides business and compliance implications
- Identifies limitations and uncertainties explicitly
- Supports audit and compliance workflows
- Never invents information outside the provided context
- Admits when context is insufficient

## GROUNDING RULES (STRICT - NON-NEGOTIABLE)

1. **USE ONLY PROVIDED CONTEXT**: Answer EXCLUSIVELY using provided context chunks. Do NOT use outside knowledge, training data, or general knowledge.

2. **NO HALLUCINATIONS**: If information is not in the context, explicitly state: "Based on the provided documents, there is insufficient information to answer this question fully."

3. **NO EXTERNAL KNOWLEDGE**: Do not use any knowledge not present in the context chunks. This includes: regulatory updates, news, general AML practices, etc.

4. **NEVER COMPLETE MISSING DATA**: If information is missing or ambiguous, state what is known and what is missing. Do not infer or guess.

5. **ALWAYS CITE SOURCES**: Every factual statement MUST be followed by the exact chunk_id from the context block.

6. **EXPLICIT CHUNK CONNECTIONS**: When your answer requires connecting information from multiple chunks, explicitly state: "Connecting information from chunk_id: [ID] and chunk_id: [ID]..."

7. **CONFIDENCE TRACKING**: Only state high confidence when multiple independent chunks confirm the same information. Use medium for single-source information, low for inferences.

## OUTPUT FORMAT (MANDATORY - JSON ONLY)

You MUST output valid JSON in this exact structure:

```json
{
  "answer": "[Direct answer to the question]",
  "reasoning": "[Analytical explanation of why and how - connect multiple chunks if needed]",
  "implications": "[Business or compliance implications - what this means for the entity]",
  "limitations": "[What is NOT covered in the documents - gaps, uncertainties, missing context]",
  "citations": ["chunk_id1", "chunk_id2", "chunk_id3"],
  "confidence": "high|medium|low"
}
```

### Section Definitions:

1. **answer**: Direct response to the question. Be concise and specific.

2. **reasoning**: 
   - Explain WHY this is the answer
   - Explain HOW the evidence leads to this conclusion
   - If using multiple chunks, explicitly connect them: "According to chunk_id: [ID], X is true. This is supported by chunk_id: [ID], which states Y. Therefore, Z."
   - Show logical flow, not just listing facts

3. **implications**: 
   - What does this mean for the business/compliance situation?
   - What are the operational or regulatory implications?
   - What actions might be required?
   - Risk considerations

4. **limitations**:
   - What information is missing from the context?
   - What questions cannot be answered?
   - What context is insufficient?
   - What uncertainties exist?
   - If no limitations: "No significant limitations identified in the provided context"

5. **citations**: List of exact chunk_ids used. Must match chunk IDs in context blocks exactly.

6. **confidence**:
   - "high": Multiple independent chunks confirm the answer, explicit evidence, no ambiguities
   - "medium": Single source but direct evidence, or multiple sources with minor inconsistencies
   - "low": Inferred from partial information, single source with gaps, or significant ambiguity

## REFUSAL POLICY

If the question cannot be answered from the provided context:
- Set "answer": "Based on the provided documents, there is insufficient information to fully answer this question."
- Set "reasoning": Explain what information is missing and why the question cannot be answered.
- Set "limitations": List the specific information gaps.
- Set "citations": []
- Set "confidence": "low"

## CRITICAL REMINDER

- Output ONLY valid JSON. No markdown, no explanations outside JSON.
- Do not use phrases like "The answer is..." or "According to the documents..."
- Be analytical, not descriptive. Explain economic/compliance logic.
- Connect at least 2 chunks when possible.
- Look like an analyst report, not a document summary."""

    def build_system_prompt(self) -> str:
        """
        Build system prompt.
        
        Returns:
            System prompt string
        """
        return self.SYSTEM_PROMPT
    
    def build_user_prompt(self, query: str, context: List[Dict]) -> str:
        """
        Build user prompt with query and structured context blocks.
        
        Args:
            query: User's question
            context: List of context items from ContextBuilder
            
        Returns:
            User prompt string
        """
        if not context:
            logger.warning("No context provided for user prompt")
            return f"""## Question
{query}

## Context
No relevant documents were found in the knowledge base.

## Instructions
Since no context chunks are available, you must output JSON with:
- "answer": "Based on the provided documents, there is insufficient information to answer this question."
- "reasoning": "No relevant documents were retrieved for this query."
- "implications": "Unable to provide implications without document context."
- "limitations": "No documents found in knowledge base for this query."
- "citations": []
- "confidence": "low\""""
        
        # Build context blocks with clear structure
        context_blocks = []
        for i, item in enumerate(context, 1):
            chunk_id = item.get("chunk_id", "unknown")
            text = item.get("text", "")
            source = item.get("source", "Unknown")
            page_numbers = item.get("metadata", {}).get("page_numbers", [])
            
            # Format page numbers
            page_info = f", page {page_numbers[0]}" if page_numbers else ""
            
            # Extract additional metadata if available
            rec_number = item.get("metadata", {}).get("recommendation_number", "")
            rec_title = item.get("metadata", {}).get("recommendation_title", "")
            
            # Build context block with metadata
            context_block = f"""---
### Context Block {i}
**chunk_id**: {chunk_id}
**source**: {source}{page_info}"""
            
            if rec_number:
                context_block += f"\n**recommendation_number**: {rec_number}"
            
            if rec_title:
                context_block += f"\n**recommendation_title**: {rec_title}"
            
            context_block += f"""

{text}
---"""
            
            context_blocks.append(context_block)
        
        context_text = "\n\n".join(context_blocks)
        
        # Build user prompt with structured format
        user_prompt = f"""## Question
{query}

## Verified Document Excerpts
You are given verified document excerpts (chunks) from regulatory or financial documents.
Each chunk comes from a regulatory or financial document.
You must reason across multiple chunks to answer.

If a conclusion requires connecting multiple parts of the document, explicitly do so.

{context_text}

## Instructions for Senior Analyst

1. **Answer using ONLY the provided context blocks above**
2. **Cite exact chunk_id for every factual statement**
3. **Connect information from multiple chunks when needed** - explicitly state: "Connecting chunk_id: [ID] and chunk_id: [ID]..."
4. **If information is not in the context blocks, state explicitly**: "Based on the provided documents, there is insufficient information to fully answer this question."
5. **Output ONLY valid JSON** - no markdown, no explanations outside JSON
6. **Follow the 6-section structure** defined in the system prompt (answer, reasoning, implications, limitations, citations, confidence)

## Reminder
- You are a senior AML/compliance analyst, not a summarizer
- Be analytical, not descriptive
- Explain economic/compliance logic
- Connect at least 2 chunks when possible
- Every claim must be supported by chunk_id"""
    
    def build_user_prompt_multi_query(
        self,
        query: str,
        context: List[Dict],
        sub_queries: Optional[List[Dict]] = None
    ) -> str:
        """
        Build user prompt with context-aware instructions.
        
        Detects scenario and adapts instructions:
        - Single query, single doc: Direct answer
        - Single query, multi-doc: Synthesize when needed OR answer from single doc
        - Multi-query: Distinct answers for each sub-question
        
        Args:
            query: Original user query
            context: List of context items from ContextBuilder
            sub_queries: Optional list from LLM decomposer (for multi-query scenarios)
            
        Returns:
            User prompt string with adaptive instructions
        """
        if not context:
            logger.warning("No context provided for user prompt")
            return self.build_user_prompt(query, context)
        
        # Detect scenario
        doc_sources = set(item.get("source", "Unknown") for item in context)
        sub_query_ids = set(item.get("metadata", {}).get("sub_query_id", -1) for item in context)
        
        is_multi_doc = len(doc_sources) > 1
        is_multi_query = len(sub_query_ids) > 1 and -1 not in sub_query_ids
        
        # Build adaptive instructions
        if is_multi_query:
            instructions = self._get_multi_query_instructions(query, sub_queries)
        elif is_multi_doc:
            instructions = self._get_multi_doc_instructions(doc_sources)
        else:
            instructions = self._get_single_query_single_doc_instructions()
        
        # Build context blocks with clear structure
        context_blocks = []
        for i, item in enumerate(context, 1):
            chunk_id = item.get("chunk_id", "unknown")
            text = item.get("text", "")
            source = item.get("source", "Unknown")
            page_numbers = item.get("metadata", {}).get("page_numbers", [])
            
            # Format page numbers
            page_info = f", page {page_numbers[0]}" if page_numbers else ""
            
            # Extract sub-query metadata if present
            sub_query_id = item.get("metadata", {}).get("sub_query_id", None)
            sub_query_text = item.get("metadata", {}).get("sub_query_text", "")
            
            # Build context block with metadata
            context_block = f"""---
### Context Block {i}
**chunk_id**: {chunk_id}
**source**: {source}{page_info}"""
            
            if sub_query_id is not None and sub_query_text:
                context_block += f"\n**sub_query_id**: {sub_query_id}"
                context_block += f"\n**sub_question**: {sub_query_text}"
            
            context_block += f"""

{text}
---"""
            
            context_blocks.append(context_block)
        
        context_text = "\n\n".join(context_blocks)
        
        # Build user prompt with structured format
        user_prompt = f"""## Original Query
{query}

## Document Sources in Context
{', '.join(sorted(doc_sources))}

{instructions}

## Verified Document Excerpts
You are given verified document excerpts (chunks) from regulatory or financial documents.
Each chunk comes from a regulatory or financial document.
You must reason across multiple chunks to answer.

{context_text}

## Instructions for Senior Analyst

1. **Answer using ONLY provided context blocks above**
2. **Cite exact chunk_id for every factual statement**
3. **Connect information from multiple chunks when needed** - explicitly state: "Connecting chunk_id: [ID] and chunk_id: [ID]..."
4. **If information is not in the context blocks, state explicitly**: "Based on the provided documents, there is insufficient information to fully answer this question."
5. **Output ONLY valid JSON** - no markdown, no explanations outside JSON
6. **Follow the 6-section structure** defined in the system prompt (answer, reasoning, implications, limitations, citations, confidence)

## Reminder
- You are a senior AML/compliance analyst, not a summarizer
- Be analytical, not descriptive
- Explain economic/compliance logic
- Connect at least 2 chunks when possible
- Every claim must be supported by chunk_id"""
        
        return user_prompt
    
    def _get_multi_query_instructions(
        self,
        query: str,
        sub_queries: Optional[List[Dict]] = None
    ) -> str:
        """
        Get instructions for multi-query scenarios.
        
        Args:
            query: Original query
            sub_queries: List of sub-queries from decomposer
            
        Returns:
            Instructions string
        """
        if sub_queries:
            sub_query_list = "\n".join([
                f"  {sq['id'] + 1}. {sq['question']}" 
                for sq in sub_queries
            ])
            instructions = f"""## Multi-Query Instructions

This query contains multiple distinct sub-questions. Answer each distinctly with clear numbering.

**Sub-questions identified:**
{sub_query_list}

**Answer Format Requirements:**
- Structure your answer to address each sub-question distinctly
- Use clear numbering: "For sub-question 1: ...", "For sub-question 2: ..."
- Each sub-question answer should be complete and standalone
- Synthesize information across documents when sub-questions require it
- If a sub-question cannot be answered, explicitly state it in the limitations"""
        else:
            instructions = """## Multi-Query Instructions

This query contains multiple distinct sub-questions. Answer each distinctly with clear numbering."""
        
        return instructions
    
    def _get_multi_doc_instructions(self, doc_sources: set) -> str:
        """
        Get instructions for multi-document scenarios.
        
        Args:
            doc_sources: Set of document source names
            
        Returns:
            Instructions string
        """
        doc_list = "\n".join([f"  - {doc}" for doc in sorted(doc_sources)])
        
        return f"""## Multi-Document Instructions

This query involves multiple documents. Synthesize information across documents when chunks from multiple documents ALL provide relevant, high-scoring evidence for the same aspect of the question.

**Documents in context:**
{doc_list}

**Synthesis Guidelines:**
- If all relevant chunks come from a single document, answer from that document
- If chunks from multiple documents ALL contribute valuable information, synthesize across documents
- Explicitly cite which document each chunk comes from
- Do NOT force synthesis across documents if evidence doesn't support it
- The goal is accurate answers, not multi-document answers"""
    
    def _get_single_query_single_doc_instructions(self) -> str:
        """
        Get instructions for single query, single document scenarios.
        
        Returns:
            Instructions string
        """
        return """## Analysis Instructions

Answer this question using the provided context directly. Focus on accuracy and clarity."""
    
    def build(self, query: str, context: List[Dict]) -> Dict[str, str]:
        """
        Build complete prompt (system + user).
        
        Args:
            query: User's question
            context: List of context items
            
        Returns:
            Dictionary with 'system' and 'user' prompts
        """
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(query, context)
        
        # Validate prompts
        if not query:
            logger.error("Query is empty")
            raise ValueError("Query cannot be empty")
        
        if not context:
            logger.warning("Building prompt with empty context")
        
        logger.info(f"Built prompt for query: '{query[:50]}...' with {len(context)} context chunks")
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def format_citation(self, chunk_id: str) -> str:
        """
        Format chunk_id as citation.
        
        Args:
            chunk_id: The chunk identifier
            
        Returns:
            Formatted citation string
        """
        return f"[chunk_id: {chunk_id}]"
    
    def validate_prompt(self, prompt: Dict[str, str]) -> bool:
        """
        Validate prompt structure.
        
        Args:
            prompt: Dictionary with 'system' and 'user' keys
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(prompt, dict):
            logger.error("Prompt must be a dictionary")
            return False
        
        if "system" not in prompt or "user" not in prompt:
            logger.error("Prompt missing 'system' or 'user' key")
            return False
        
        if not prompt["system"] or not prompt["user"]:
            logger.error("System or user prompt is empty")
            return False
        
        return True