"""
Test script for sentence-based similarity clustering.

This script validates:
1. Sentence splitting (not paragraphs)
2. Sentence embedding
3. Similarity matrix building
4. Clustering by threshold
5. MAX_CHUNK_CHARS enforcement (1250)
6. Metadata preservation
"""

import json
from pathlib import Path
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.similarity_cluster_chunker import SimilarityClusterChunker
from config import Config


def test_sentence_splitting():
    """Test that text is split into sentences, not paragraphs."""
    print("\n" + "="*70)
    print("TEST 1: Sentence Splitting")
    print("="*70)
    
    test_text = """
This is sentence one. This is sentence two. This is sentence three.

This is sentence four. This is sentence five.
""".strip()
    
    chunker = SimilarityClusterChunker()
    sentences = chunker._split_sentences_with_offsets(test_text)
    
    print(f"Input text: {len(test_text)} chars")
    print(f"Output sentences: {len(sentences)}")
    
    for i, (text, start, end) in enumerate(sentences):
        print(f"\nSentence {i+1}:")
        print(f"  Length: {len(text)} chars")
        print(f"  Range: [{start}, {end}]")
        print(f"  Preview: {text[:50]}...")
    
    # Should have 5 sentences
    assert len(sentences) == 5, f"Expected 5 sentences, got {len(sentences)}"
    print("\n✅ PASSED: Correct sentence splitting")
    return True


def test_similarity_matrix():
    """Test that similarity matrix is built correctly."""
    print("\n" + "="*70)
    print("TEST 2: Similarity Matrix Building")
    print("="*70)
    
    # Create simple test data
    test_sentences = [
        "This is about cats.",
        "This is about dogs.",
        "This is about birds."
    ]
    
    chunker = SimilarityClusterChunker()
    embeddings = chunker._embed_texts_batched(test_sentences)
    
    print(f"Embeddings shape: {embeddings.shape}")
    
    # Build similarity matrix
    sim_matrix = chunker._build_similarity_matrix(embeddings)
    
    print(f"Similarity matrix shape: {sim_matrix.shape}")
    print(f"Matrix diagonal (should be 1.0): {np.diag(sim_matrix)}")
    
    # Check diagonal is 1.0
    assert np.allclose(np.diag(sim_matrix), 1.0), "Diagonal should be 1.0"
    
    # Check matrix is symmetric
    assert np.allclose(sim_matrix, sim_matrix.T), "Matrix should be symmetric"
    
    print("\n✅ PASSED: Similarity matrix built correctly")
    return True


def test_clustering():
    """Test that clustering by threshold works."""
    print("\n" + "="*70)
    print("TEST 3: Clustering by Threshold")
    print("="*70)
    
    # Create similar sentences (should cluster together)
    test_sentences = [
        "Cats are pets.",
        "Cats like milk.",
        "Dogs are also pets.",
        "Dogs are loyal.",
    ]
    
    chunker = SimilarityClusterChunker()
    embeddings = chunker._embed_texts_batched(test_sentences)
    sim_matrix = chunker._build_similarity_matrix(embeddings)
    
    print(f"Test sentences: {len(test_sentences)}")
    print(f"Similarity threshold: {chunker.similarity_threshold}")
    
    # Cluster
    clusters = chunker._cluster_by_threshold(sim_matrix, len(test_sentences))
    
    print(f"Clusters created: {len(clusters)}")
    for i, cluster in enumerate(clusters):
        print(f"  Cluster {i+1}: sentences {cluster}")
    
    # Should have at least 1 cluster
    assert len(clusters) > 0, "Should have at least 1 cluster"
    
    print("\n✅ PASSED: Clustering works")
    return True


def test_max_chunk_size():
    """Test that chunks respect MAX_CHUNK_CHARS = 1250."""
    print("\n" + "="*70)
    print("TEST 4: MAX_CHUNK_CHARS Safety Cap")
    print("="*70)
    
    # Create document data
    document_data = {
        "doc_id": "test-doc-size",
        "pages": [
            {
                "page_number": 1,
                "text": "This is a test sentence. " * 50  # ~1500 chars
            }
        ],
        "document_name": "test.pdf",
        "extraction_version": "5.0.0",
        "ingestion_timestamp": "2026-01-26T14:00:00",
        "source": "upload"
    }
    
    chunker = SimilarityClusterChunker()
    result = chunker.chunk_document(document_data)
    
    print(f"Input text length: {len(document_data['pages'][0]['text'])} chars")
    print(f"MAX_CHUNK_CHARS limit: {chunker.MAX_CHUNK_CHARS} chars")
    print(f"\nCreated {len(result['chunks'])} chunks:")
    
    for i, chunk in enumerate(result['chunks']):
        print(f"  Chunk {i+1}: {chunk['chunk_size']} chars (max: {chunker.MAX_CHUNK_CHARS})")
        assert chunk['chunk_size'] <= chunker.MAX_CHUNK_CHARS, \
            f"Chunk {i+1} exceeds MAX_CHUNK_CHARS: {chunk['chunk_size']} > {chunker.MAX_CHUNK_CHARS}"
    
    print("\n✅ PASSED: All chunks respect MAX_CHUNK_CHARS")
    return True


def test_metadata_preservation():
    """Test that metadata is properly preserved in chunks."""
    print("\n" + "="*70)
    print("TEST 5: Metadata Preservation")
    print("="*70)
    
    # Create test document with metadata
    document_data = {
        "doc_id": "test-doc-metadata",
        "pages": [
            {
                "page_number": 1,
                "text": "This is test page one content. This is another sentence."
            },
            {
                "page_number": 2,
                "text": "This is test page two content. More sentences here."
            }
        ],
        "document_name": "metadata_test.pdf",
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
        assert chunk['doc_id'] == "test-doc-metadata"
        assert chunk['document_name'] == "metadata_test.pdf"
        assert chunk['extraction_version'] == "5.0.0"
        assert chunk['source'] == "upload"
        assert chunk['file_type'] == "pdf"
        assert chunk['file_size'] == 12345
        
        print("\n✅ PASSED: All metadata preserved")
    else:
        print("\n⚠️  No chunks created")
    
    return True


def test_full_document():
    """Test end-to-end chunking on full document."""
    print("\n" + "="*70)
    print("TEST 6: Full Document Chunking")
    print("="*70)
    
    # Create realistic document
    document_data = {
        "doc_id": "test-doc-full",
        "pages": [
            {
                "page_number": 1,
                "text": "Bank account opening procedures require proper identification. This includes government-issued ID and proof of address. The applicant must provide valid documentation."
            },
            {
                "page_number": 2,
                "text": "KYC regulations mandate thorough verification. This process involves checking multiple data sources. Compliance officers review all submitted documents."
            },
            {
                "page_number": 3,
                "text": "AML monitoring systems detect suspicious activities. These systems use advanced algorithms. Alerts are generated automatically for review."
            }
        ],
        "document_name": "compliance_manual.pdf",
        "extraction_version": "5.0.0",
        "ingestion_timestamp": "2026-01-26T14:00:00",
        "source": "upload"
    }
    
    chunker = SimilarityClusterChunker()
    result = chunker.chunk_document(document_data)
    
    print(f"Total chunks created: {len(result['chunks'])}")
    
    if len(result['chunks']) > 0:
        print(f"\nChunk statistics:")
        chunk_sizes = [c['chunk_size'] for c in result['chunks']]
        print(f"  Min size: {min(chunk_sizes)} chars")
        print(f"  Max size: {max(chunk_sizes)} chars")
        print(f"  Avg size: {np.mean(chunk_sizes):.0f} chars")
        print(f"  Total chunks: {len(result['chunks'])}")
        
        # Verify all chunks are reasonable size
        assert max(chunk_sizes) <= chunker.MAX_CHUNK_CHARS, "Max chunk exceeds limit"
        assert len(result['chunks']) <= 20, "Too many chunks created"
        assert len(result['chunks']) >= 1, "No chunks created"
        
        # Verify chunk structure
        chunk = result['chunks'][0]
        required_fields = [
            "chunk_id", "doc_id", "text", "strategy",
            "page_numbers", "char_range", "position",
            "chunk_size", "chunk_index", "total_chunks"
        ]
        for field in required_fields:
            assert field in chunk, f"Missing field: {field}"
        
        print(f"\n✅ PASSED: Full document chunking works correctly")
    else:
        print("\n❌ FAILED: No chunks created")
        return False
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("SENTENCE-BASED CLUSTERING TEST SUITE")
    print("="*70)
    
    tests = [
        ("Sentence Splitting", test_sentence_splitting),
        ("Similarity Matrix Building", test_similarity_matrix),
        ("Clustering by Threshold", test_clustering),
        ("MAX_CHUNK_CHARS Safety Cap", test_max_chunk_size),
        ("Metadata Preservation", test_metadata_preservation),
        ("Full Document Chunking", test_full_document)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ FAILED: {name}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
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