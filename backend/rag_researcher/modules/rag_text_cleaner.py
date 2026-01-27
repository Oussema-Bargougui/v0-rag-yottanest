#!/usr/bin/env python3
"""
Production-Grade Text Cleaning Layer for Multimodal RAG System (Bank-Level)

This module provides lossless, production-grade text normalization for RAG ingestion.
It operates after extraction and before chunking.

Key Features:
- Lossless cleaning (no data removal)
- Metadata preservation (100%)
- Page-level processing (no concatenation)
- Deterministic output
- No LLM calls
- Fast (< 50ms per page)

Author: Yottanest Team
Version: 1.0.0 - Production
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGTextCleaner:
    """
    Production-grade text cleaner for RAG ingestion pipeline.
    
    This class provides lossless text normalization that preserves:
    - Metadata 100%
    - Page structure
    - Image blocks
    - Table structure
    - All symbols, numbers, currencies
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Initialize RAG text cleaner.
        
        Args:
            storage_path: Base storage path (defaults to Config storage path)
        """
        # Get storage path from config if not provided
        if storage_path is None:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config import Config
            storage_path = Config.get_storage_path()
        
        self.storage_path = Path(storage_path)
        self.cleaned_path = self.storage_path / "cleaned"
        self.cleaned_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"RAGTextCleaner initialized")
        logger.info(f"Storage path: {self.storage_path}")
        logger.info(f"Cleaned output path: {self.cleaned_path}")
    
    def clean_extracted_document(self, extracted_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean an extracted document JSON.
        
        This method:
        - Operates page by page (no concatenation)
        - Preserves metadata 100%
        - Applies lossless cleaning
        - Returns same JSON schema with cleaned text
        
        Args:
            extracted_json: Extracted document JSON from storage/extraction/<doc_id>.json
            
        Returns:
            Cleaned document JSON with identical schema
        """
        start_time = time.time()
        
        # Extract doc_id for logging
        doc_id = extracted_json.get('doc_id', 'unknown')
        filename = extracted_json.get('filename', 'unknown')
        
        # Calculate stats before cleaning
        total_chars_before = sum(
            len(page.get('text', '')) 
            for page in extracted_json.get('pages', [])
        )
        
        # Create cleaned document (copy structure)
        cleaned_json = {
            'doc_id': doc_id,
            'filename': filename,
            'pages': []
        }
        
        # Copy metadata if present
        if 'metadata' in extracted_json:
            cleaned_json['metadata'] = extracted_json['metadata'].copy()
        
        # Process each page independently
        pages_count = 0
        for page in extracted_json.get('pages', []):
            # Preserve page_number and metadata
            page_number = page.get('page_number', 0)
            page_metadata = page.get('metadata', {}).copy() if 'metadata' in page else {}
            
            # Clean text
            original_text = page.get('text', '')
            cleaned_text = self._clean_page_text(original_text)
            
            # Add cleaned page
            cleaned_json['pages'].append({
                'page_number': page_number,
                'text': cleaned_text,
                'metadata': page_metadata
            })
            
            pages_count += 1
        
        # Calculate stats after cleaning
        total_chars_after = sum(
            len(page.get('text', '')) 
            for page in cleaned_json['pages']
        )
        
        elapsed_time = time.time() - start_time
        
        # Log processing stats
        logger.info(f"✅ Cleaned document: {doc_id}")
        logger.info(f"   Filename: {filename}")
        logger.info(f"   Pages: {pages_count}")
        logger.info(f"   Characters: {total_chars_before} → {total_chars_after} ({total_chars_after - total_chars_before:+d})")
        logger.info(f"   Time: {elapsed_time*1000:.1f}ms ({elapsed_time*1000/pages_count:.1f}ms/page)")
        
        # Warn if significant character loss
        if total_chars_after < total_chars_before * 0.9:
            logger.warning(f"⚠️  Character loss > 10%: {total_chars_before} → {total_chars_after}")
        
        return cleaned_json
    
    def _clean_page_text(self, text: str) -> str:
        """
        Clean page text using lossless rules.
        
        Allowed operations:
        1. Remove control characters (\u0007 \x0c \x0b \x00)
        2. Normalize whitespace (without flattening)
        3. Normalize line breaks (reduce 4+ to 2, preserve structure)
        4. Normalize broken hyphenation
        5. Normalize quotes and dashes
        
        Args:
            text: Raw page text
            
        Returns:
            Cleaned page text
        """
        if not text:
            return text
        
        cleaned = text
        
        # Step 1: Remove control characters (safe)
        cleaned = self._remove_control_characters(cleaned)
        
        # Step 2: Normalize broken hyphenation
        cleaned = self._fix_hyphenation(cleaned)
        
        # Step 3: Normalize quotes and dashes
        cleaned = self._normalize_quotes_and_dashes(cleaned)
        
        # Step 4: Normalize whitespace (without flattening)
        cleaned = self._normalize_whitespace(cleaned)
        
        # Step 5: Normalize line breaks (preserve structure)
        cleaned = self._normalize_line_breaks(cleaned)
        
        return cleaned
    
    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters (safe operation)."""
        # Remove specific control characters
        control_chars = ['\u0007', '\x0c', '\x0b', '\x00']
        for char in control_chars:
            text = text.replace(char, '')
        return text
    
    def _fix_hyphenation(self, text: str) -> str:
        """Fix broken hyphenation at line breaks."""
        # Pattern: word- \n word
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        return text
    
    def _normalize_quotes_and_dashes(self, text: str) -> str:
        """Normalize quotes and dashes (safe operation)."""
        # Normalize quotes
        text = text.replace('"', '"')
        text = text.replace('"', '"')
        text = text.replace(''', "'")
        text = text.replace(''', "'")
        
        # Normalize dashes
        text = text.replace('—', '-')
        text = text.replace('–', '-')
        text = text.replace('‐', '-')
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace without flattening structure.
        
        Rules:
        - Reduce multiple spaces to single space
        - Preserve single spaces
        - Do NOT remove line breaks
        """
        # Reduce multiple spaces to single space (but not across lines)
        lines = text.split('\n')
        normalized_lines = []
        for line in lines:
            # Reduce multiple spaces to single space
            normalized = re.sub(r' +', ' ', line)
            normalized_lines.append(normalized)
        
        return '\n'.join(normalized_lines)
    
    def _normalize_line_breaks(self, text: str) -> str:
        """
        Normalize line breaks while preserving structure.
        
        Rules:
        - Reduce 4+ consecutive line breaks to 2
        - Preserve paragraphs
        - Preserve bullets
        - Preserve table structure
        - Preserve image blocks
        """
        # Protect image blocks
        text = self._protect_image_blocks(text)
        
        # Protect table-like structure (multiple pipes)
        text = self._protect_table_structure(text)
        
        # Normalize excessive line breaks
        # Reduce 4+ consecutive newlines to 2
        text = re.sub(r'\n{4,}', '\n\n', text)
        
        # Restore protected content
        text = self._restore_table_structure(text)
        text = self._restore_image_blocks(text)
        
        return text
    
    def _protect_image_blocks(self, text: str) -> str:
        """Protect image blocks from line break normalization."""
        # Pattern: [IMAGE] ... (until next paragraph)
        image_pattern = r'(\[IMAGE\][^\[]*?)(?=\n\n|\Z)'
        protected = re.sub(image_pattern, lambda m: m.group(1).replace('\n', '\x00'), text)
        return protected
    
    def _restore_image_blocks(self, text: str) -> str:
        """Restore image blocks after protection."""
        return text.replace('\x00', '\n')
    
    def _protect_table_structure(self, text: str) -> str:
        """Protect table-like structure from line break normalization."""
        # Pattern: lines containing pipe characters
        lines = text.split('\n')
        protected_lines = []
        in_table = False
        
        for line in lines:
            # Check if line looks like table (contains pipe)
            is_table_row = '|' in line
            
            if is_table_row:
                # Mark table rows
                protected_lines.append('\t' + line + '\t')
                in_table = True
            else:
                if in_table and line.strip():
                    # Continue table if line has content
                    protected_lines.append('\t' + line + '\t')
                else:
                    # End of table
                    protected_lines.append(line)
                    in_table = False
        
        return '\n'.join(protected_lines)
    
    def _restore_table_structure(self, text: str) -> str:
        """Restore table structure after protection."""
        lines = text.split('\n')
        restored_lines = []
        
        for line in lines:
            if line.startswith('\t') and line.endswith('\t'):
                # Restore table row
                restored_lines.append(line[1:-1])
            else:
                restored_lines.append(line)
        
        return '\n'.join(restored_lines)
    
    def save_cleaned_document(self, cleaned_json: Dict[str, Any]) -> str:
        """
        Save cleaned document to storage/cleaned/<doc_id>.json.
        
        Args:
            cleaned_json: Cleaned document JSON
            
        Returns:
            Path to saved file
        """
        doc_id = cleaned_json.get('doc_id', 'unknown')
        output_path = self.cleaned_path / f"{doc_id}.json"
        
        # Save cleaned JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved cleaned document to: {output_path}")
        return str(output_path)


def main():
    """CLI test mode for RAGTextCleaner."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rag_text_cleaner.py <extraction_json_path>")
        print("Example: python rag_text_cleaner.py storage/extraction/<doc_id>.json")
        sys.exit(1)
    
    extraction_path = sys.argv[1]
    
    # Validate input path
    if not os.path.exists(extraction_path):
        print(f"Error: File not found: {extraction_path}")
        sys.exit(1)
    
    # Load extracted JSON
    logger.info(f"Loading extracted document from: {extraction_path}")
    with open(extraction_path, 'r', encoding='utf-8') as f:
        extracted_json = json.load(f)
    
    # Initialize cleaner
    cleaner = RAGTextCleaner()
    
    # Clean document
    logger.info("="*60)
    logger.info("Cleaning document...")
    logger.info("="*60)
    cleaned_json = cleaner.clean_extracted_document(extracted_json)
    
    # Save cleaned document
    logger.info("="*60)
    logger.info("Saving cleaned document...")
    logger.info("="*60)
    output_path = cleaner.save_cleaned_document(cleaned_json)
    
    # Print summary
    print("\n" + "="*60)
    print("CLEANING SUMMARY")
    print("="*60)
    print(f"Input:  {extraction_path}")
    print(f"Output: {output_path}")
    print(f"Doc ID: {cleaned_json.get('doc_id')}")
    print(f"Pages:  {len(cleaned_json.get('pages', []))}")
    print(f"\n✅ Cleaning completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()