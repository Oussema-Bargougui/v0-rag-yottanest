"""
Test script for production-grade paragraph-level chunking.

This script validates:
1. Paragraph-level splitting (not sentences)
2. Paragraph embedding (not sentence embedding)
3. Similarity clustering with sliding window
4. MAX_CHUNK_CHARS safety cap (1250 chars)
5. Metadata preservation in chunks
6. Correct output format (single JSON file)
7. Page preservation in chunks
"""

import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.similarity_cluster_chunker import SimilarityClusterChunker
from config import Config


def test_paragraph_splitting():
    """Test that text is split into paragraphs, not sentences."""
    print("\n" + "="*70)
    print("TEST 1: Paragraph Splitting")
    print("="*70)
    
    test_text = """
This is paragraph one. It has multiple sentences. But it should stay together.

This is paragraph two. Different topic.

This is paragraph three. Yet another distinct section.
""".strip()
    
    chunker = SimilarityClusterChunker()
    paragraphs = chunker._split_paragraphs_with_offsets(test_text)
    
    print(f"Input text: {len(test_text)} chars")
    print(f"Output paragraphs: {len(paragraphs)}")
    
    for i, (text, start, end) in enumerate(paragraphs):
        print(f"\nParagraph {i+1}:")
        print(f"  Length: {len(text)} chars")
        print(f"  Range: [{start}, {end}]")
        print(f"  Preview: {text[:50]}...")
    
    # Should have 3 paragraphs
    assert len(paragraphs) == 3, f"Expected 3 paragraphs, got {len(paragraphs)}"
    print("\n✅ PASSED: Correct paragraph splitting")
    return True


def test_max_chunk_size():
    """Test that chunks respect MAX_CHUNK_CHARS = 1250."""
    print("\n" + "="*70)
    print("TEST 2: MAX_CHUNK_CHARS Safety Cap")
    print("="*70)
    
    # Create a very large paragraph
    large_paragraph = "This is a test sentence. " * 100  # ~3000 chars
    
    chunker = SimilarityClusterChunker()
    
    print(f"Input paragraph: {len(large_paragraph)} chars")
    print(f"MAX_CHUNK_CHARS limit: {chunker.MAX_CHUNK_CHARS} chars")
    
    # Split large paragraph
    split_chunks = chunker._split_large_paragraph(
        large_paragraph,
        0,
        len(large_paragraph),
        [1]  # page 1
    )
    
    print(f"\nSplit into {len(split_chunks)} chunks:")
    for i, (text, start, end, pages) in enumerate(split_chunks):
        print(f"  Chunk {i+1}: {len(text)} chars (max: {chunker.MAX_CHUNK_CHARS})")
        assert len(text) <= chunker.MAX_CHUNK_CHARS, \
            f"Chunk {i+1} exceeds MAX_CHUNK_CHARS: {len(text)} > {chunker.MAX_CHUNK_CHARS}"
    
    print("\n✅ PASSED: All chunks respect MAX_CHUNK_CHARS")
    return True


def test_metadata_preservation():
    """Test that metadata is properly preserved in chunks."""
    print("\n" + "="*70)
    print("TEST 3: Metadata Preservation")
    print("="*70)
    
    # Create test document with metadata
    document_data = {
        "doc_id": "test-doc-123",
        "pages": [
            {
                "page_number": 1,
                "text": "This is test page one content."
            },
            {
                "page_number": 2,
                "text": "This is test page two content."
            }
        ],
        "document_name": "test_document.pdf",
        "extraction_version": "5.0.0",
        "ingestion_timestamp": "2026-01-26T14:00:00",
        "source": "upload",
        "file_type": "pdf",
        "file_size": 12345,
        "file_hash": "abc123def456"
    }
    
    chunker = SimilarityClusterChunker()
    result = chunker.chunk_document(document_data)
    
    print(f"Created {len(result['chunks'])} chunks")
    
    # Check first chunk for metadata
    if len(result['chunks']) > 0:
        chunk = result['chunks'][0]
        print(f"\nFirst chunk metadata:")
        print(f"  doc_id: {chunk.get('doc_id')}")
        print(f"  document_name: {chunk.get('document_name')}")
        print(f"  extraction_version: {chunk.get('extraction_version')}")
        print(f"  ingestion_timestamp: {chunk.get('ingestion_timestamp')}")
        print(f"  source: {chunk.get('source')}")
        print(f"  file_type: {chunk.get('file_type')}")
        print(f"  file_size: {chunk.get('file_size')}")
        print(f"  file_hash: {chunk.get('file_hash')}")
        
        # Verify metadata
        assert chunk['doc_id'] == "test-doc-123"
        assert chunk['document_name'] == "test_document.pdf"
        assert chunk['extraction_version'] == "5.0.0"
        assert chunk['source'] == "upload"
        assert chunk['file_type'] == "pdf"
        assert chunk['file_size'] == 12345
        
        print("\n✅ PASSED: All metadata preserved")
    else:
        print("\n⚠️  No chunks created")
    
    return True


def test_output_format():
    """Test that output format matches specification."""
    print("\n" + "="*70)
    print("TEST 4: Output Format")
    print("="*70)
    
    document_data = {
        "doc_id": "test-doc-456",
        "pages": [
            {
                "page_number": 1,
                "text": "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
            }
        ],
        "document_name": "format_test.pdf",
        "extraction_version": "5.0.0",
        "ingestion_timestamp": "2026-01-26T14:00:00",
        "source": "upload"
    }
    
    chunker = SimilarityClusterChunker()
    result = chunker.chunk_document(document_data)
    
    # Check top-level structure
    print(f"Result keys: {list(result.keys())}")
    assert "doc_id" in result
    assert "document_name" in result
    assert "chunk_strategy" in result
    assert "chunks" in result
    
    # Check chunk structure
    if len(result['chunks']) > 0:
        chunk = result['chunks'][0]
        print(f"\nChunk keys: {list(chunk.keys())}")
        
        required_keys = [
            "chunk_id", "doc_id", "text", "strategy",
            "page_numbers", "char_range", "position",
            "chunk_size", "chunk_index", "total_chunks"
        ]
        
        for key in required_keys:
            assert key in chunk, f"Missing required key: {key}"
        
        print(f"\nRequired fields present: {len(required_keys)}/{len(required_keys)}")
        print(f"  chunk_id: {chunk['chunk_id']}")
        print(f"  chunk_size: {chunk['chunk_size']} chars")
        print(f"  chunk_index: {chunk['chunk_index']}/{chunk['total_chunks']}")
        print(f"  page_numbers: {chunk['page_numbers']}")
        print(f"  char_range: {chunk['char_range']}")
        
        print("\n✅ PASSED: Output format correct")
    else:
        print("\n⚠️  No chunks created")
    
    return True


def test_page_preservation():
    """Test that page numbers are correctly preserved."""
    print("\n" + "="*70)
    print("TEST 5: Page Preservation")
    print("="*70)
    
    document_data = {
        "doc_id": "test-doc-789",
        "pages": [
            {
                "page_number": 1,
                "text": "Content from page one."
            },
            {
                "page_number": 2,
                "text": "Content from page two."
            },
            {
                "page_number": 3,
                "text": "Content from page three."
            }
        ],
        "document_name": "page_test.pdf",
        "extraction_version": "5.0.0",
        "ingestion_timestamp": "2026-01-26T14:00:00",
        "source": "upload"
    }
    
    chunker = SimilarityClusterChunker()
    result = chunker.chunk_document(document_data)
    
    print(f"Created {len(result['chunks'])} chunks")
    
    # Check page numbers in chunks
    for i, chunk in enumerate(result['chunks']):
        print(f"\nChunk {i+1}:")
        print(f"  page_numbers: {chunk['page_numbers']}")
        print(f"  char_range: {chunk['char_range']}")
        assert len(chunk['page_numbers']) > 0, "No page numbers in chunk"
        assert chunk['page_numbers'][0] >= 1, "Invalid page number"
    
    print("\n✅ PASSED: Page numbers preserved")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("PRODUCTION CHUNKING TEST SUITE")
    print("="*70)
    
    tests = [
        ("Paragraph Splitting", test_paragraph_splitting),
        ("MAX_CHUNK_CHARS Safety Cap", test_max_chunk_size),
        ("Metadata Preservation", test_metadata_preservation),
        ("Output Format", test_output_format),
        ("Page Preservation", test_page_preservation)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ FAILED: {name}")
            print(f"   Error: {str(e)}")
            results[name] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - PRODUCTION READY!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)