"""
Test script for chunking implementations.

Tests both SemanticPercentileChunker and SimilarityClusterChunker
to ensure they work correctly with sample data.
"""

import json
import os
from pathlib import Path
from modules.semantic_percentile_chunker import SemanticPercentileChunker
from modules.similarity_cluster_chunker import SimilarityClusterChunker


def create_sample_document():
    """
    Create a sample document with multiple pages for testing.
    """
    doc_id = "test-doc-123"
    
    # Sample text spanning multiple pages with different topics
    pages = [
        {
            "page_number": 1,
            "text": """Banking regulations are critical for financial stability. The Basel III framework establishes comprehensive capital requirements for banks worldwide. These requirements ensure that institutions maintain adequate capital buffers to absorb losses during economic downturns. The framework also includes liquidity requirements and leverage ratios to strengthen the banking sector's resilience.""",
            "metadata": {"source": "test.pdf"}
        },
        {
            "page_number": 2,
            "text": """Anti-Money Laundering (AML) regulations require financial institutions to implement robust monitoring systems. These systems must detect suspicious transactions and report them to relevant authorities. The Financial Action Task Force (FATF) sets international standards for AML and Counter-Terrorist Financing (CTF) measures. Compliance with these standards is mandatory for banks operating in the global financial system.""",
            "metadata": {"source": "test.pdf"}
        },
        {
            "page_number": 3,
            "text": """Know Your Customer (KYC) procedures are essential components of banking compliance. Banks must verify the identity of their clients and assess their risk profiles. This process involves collecting personal information, proof of address, and understanding the nature of the customer's business activities. Effective KYC procedures help prevent fraud and ensure regulatory compliance.""",
            "metadata": {"source": "test.pdf"}
        },
        {
            "page_number": 4,
            "text": """Risk management in banking involves identifying, assessing, and mitigating various types of risks. Credit risk, market risk, and operational risk are the primary categories. Banks use sophisticated models and stress testing to evaluate their risk exposure. The risk management framework must be aligned with the institution's strategic objectives and regulatory requirements.""",
            "metadata": {"source": "test.pdf"}
        }
    ]
    
    return {
        "doc_id": doc_id,
        "document_name": "test_document.pdf",
        "pages": pages
    }


def test_semantic_percentile_chunker():
    """
    Test the Semantic Percentile Chunker.
    """
    print("=" * 80)
    print("Testing Semantic Percentile Chunker")
    print("=" * 80)
    
    # Create chunker with production parameters
    chunker = SemanticPercentileChunker(
        min_tokens=150,
        max_tokens=800,
        percentile_threshold=25.0
    )
    
    # Create sample document
    document = create_sample_document()
    
    print(f"\nDocument ID: {document['doc_id']}")
    print(f"Total pages: {len(document['pages'])}")
    print(f"Total characters: {sum(len(p['text']) for p in document['pages'])}")
    
    # Chunk the document
    chunks = chunker.chunk_document(document)
    
    print(f"\nNumber of chunks created: {len(chunks)}")
    
    # Display chunk details
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Strategy: {chunk['strategy']}")
        print(f"Position: {chunk['position']}")
        print(f"Pages: {chunk['page_numbers']}")
        print(f"Character range: {chunk['char_range']}")
        print(f"Text length: {len(chunk['text'])} chars")
        print(f"Estimated tokens: {chunk['text'].split().__len__()}")
        print(f"Preview: {chunk['text'][:200]}...")
    
    # Validate chunks
    print("\n" + "=" * 80)
    print("Validation:")
    print("=" * 80)
    
    all_valid = True
    
    for i, chunk in enumerate(chunks):
        # Check required fields
        required_fields = ['chunk_id', 'doc_id', 'text', 'strategy', 'page_numbers', 'char_range', 'position']
        for field in required_fields:
            if field not in chunk:
                print(f"✗ Chunk {i}: Missing field '{field}'")
                all_valid = False
        
        # Check page boundaries are preserved
        if not chunk['page_numbers']:
            print(f"✗ Chunk {i}: No page numbers")
            all_valid = False
        
        # Check token limits
        tokens = chunk['text'].split().__len__()
        if tokens < 150:
            print(f"⚠ Chunk {i}: Below min_tokens ({tokens} < 150)")
        elif tokens > 800:
            print(f"✗ Chunk {i}: Exceeds max_tokens ({tokens} > 800)")
            all_valid = False
    
    if all_valid:
        print("✓ All chunks are valid")
    
    return chunks


def test_similarity_cluster_chunker():
    """
    Test the Similarity Cluster Chunker.
    """
    print("\n\n")
    print("=" * 80)
    print("Testing Similarity Cluster Chunker")
    print("=" * 80)
    
    # Create chunker with production parameters
    chunker = SimilarityClusterChunker(
        min_tokens=150,
        max_tokens=800,
        similarity_threshold=0.75
    )
    
    # Create sample document
    document = create_sample_document()
    
    print(f"\nDocument ID: {document['doc_id']}")
    print(f"Total pages: {len(document['pages'])}")
    print(f"Total characters: {sum(len(p['text']) for p in document['pages'])}")
    
    # Chunk the document
    chunks = chunker.chunk_document(document)
    
    print(f"\nNumber of chunks created: {len(chunks)}")
    
    # Display chunk details
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Strategy: {chunk['strategy']}")
        print(f"Position: {chunk['position']}")
        print(f"Pages: {chunk['page_numbers']}")
        print(f"Character range: {chunk['char_range']}")
        print(f"Text length: {len(chunk['text'])} chars")
        print(f"Estimated tokens: {chunk['text'].split().__len__()}")
        print(f"Preview: {chunk['text'][:200]}...")
    
    # Validate chunks
    print("\n" + "=" * 80)
    print("Validation:")
    print("=" * 80)
    
    all_valid = True
    
    for i, chunk in enumerate(chunks):
        # Check required fields
        required_fields = ['chunk_id', 'doc_id', 'text', 'strategy', 'page_numbers', 'char_range', 'position']
        for field in required_fields:
            if field not in chunk:
                print(f"✗ Chunk {i}: Missing field '{field}'")
                all_valid = False
        
        # Check page boundaries are preserved
        if not chunk['page_numbers']:
            print(f"✗ Chunk {i}: No page numbers")
            all_valid = False
        
        # Check token limits
        tokens = chunk['text'].split().__len__()
        if tokens < 150:
            print(f"⚠ Chunk {i}: Below min_tokens ({tokens} < 150)")
        elif tokens > 800:
            print(f"✗ Chunk {i}: Exceeds max_tokens ({tokens} > 800)")
            all_valid = False
    
    if all_valid:
        print("✓ All chunks are valid")
    
    return chunks


def compare_chunkers():
    """
    Compare the outputs of both chunkers.
    """
    print("\n\n")
    print("=" * 80)
    print("Comparing Chunkers")
    print("=" * 80)
    
    document = create_sample_document()
    
    # Create chunkers
    percentile_chunker = SemanticPercentileChunker(min_tokens=150, max_tokens=800, percentile_threshold=25.0)
    cluster_chunker = SimilarityClusterChunker(min_tokens=150, max_tokens=800, similarity_threshold=0.75)
    
    # Get chunks from both
    percentile_chunks = percentile_chunker.chunk_document(document)
    cluster_chunks = cluster_chunker.chunk_document(document)
    
    print(f"\nSemantic Percentile Chunker: {len(percentile_chunks)} chunks")
    print(f"Similarity Cluster Chunker: {len(cluster_chunks)} chunks")
    
    # Calculate average chunk sizes
    percentile_avg = sum(len(c['text']) for c in percentile_chunks) / len(percentile_chunks) if percentile_chunks else 0
    cluster_avg = sum(len(c['text']) for c in cluster_chunks) / len(cluster_chunks) if cluster_chunks else 0
    
    print(f"\nAverage chunk size:")
    print(f"  Semantic Percentile: {percentile_avg:.0f} chars")
    print(f"  Similarity Cluster: {cluster_avg:.0f} chars")
    
    # Check page boundary crossing
    percentile_crosses = sum(1 for c in percentile_chunks if len(c['page_numbers']) > 1)
    cluster_crosses = sum(1 for c in cluster_chunks if len(c['page_numbers']) > 1)
    
    print(f"\nChunks crossing page boundaries:")
    print(f"  Semantic Percentile: {percentile_crosses}/{len(percentile_chunks)}")
    print(f"  Similarity Cluster: {cluster_crosses}/{len(cluster_chunks)}")


def main():
    """
    Run all tests.
    """
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "RAG CHUNKING TEST SUITE" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        # Test Semantic Percentile Chunker
        percentile_chunks = test_semantic_percentile_chunker()
        
        # Test Similarity Cluster Chunker
        cluster_chunks = test_similarity_cluster_chunker()
        
        # Compare both
        compare_chunkers()
        
        print("\n\n")
        print("=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)
        
        # Save sample output
        output_dir = Path("output/chunking")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "percentile_chunks.json", "w") as f:
            json.dump(percentile_chunks, f, indent=2)
        
        with open(output_dir / "cluster_chunks.json", "w") as f:
            json.dump(cluster_chunks, f, indent=2)
        
        print(f"\n✓ Sample outputs saved to {output_dir}/")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()