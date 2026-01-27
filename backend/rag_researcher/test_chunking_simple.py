"""
Simple test to verify chunking integration without embedding API.

This tests the chunkers with fallback behavior when embedding fails.
"""

from modules.semantic_percentile_chunker import SemanticPercentileChunker
from modules.similarity_cluster_chunker import SimilarityClusterChunker


def test_chunking_simple():
    """Test chunking with a simple document."""
    
    # Create test document
    document = {
        "doc_id": "test-doc-123",
        "filename": "test.txt",
        "pages": [
            {
                "page_number": 1,
                "text": """Banking regulations are critical for financial stability. The Basel III framework establishes comprehensive capital requirements for banks worldwide. These requirements ensure that institutions maintain adequate capital buffers to absorb losses during economic downturns.
                
Anti-Money Laundering (AML) regulations require financial institutions to implement robust monitoring systems. These systems must detect suspicious transactions and report them to relevant authorities. The Financial Action Task Force (FATF) sets international standards for AML and Counter-Terrorist Financing (CTF) measures.

Know Your Customer (KYC) procedures are essential components of banking compliance. Banks must verify the identity of their clients and assess their risk profiles. This process involves collecting personal information, proof of address, and understanding the nature of the customer's business activities.

Risk management in banking involves identifying, assessing, and mitigating various types of risks. Credit risk, market risk, and operational risk are the primary categories. Banks use sophisticated models and stress testing to evaluate their risk exposure."""
            }
        ]
    }
    
    print("=" * 80)
    print("Testing Chunking Integration")
    print("=" * 80)
    
    # Test semantic percentile chunking
    print("\n1. Testing Semantic Percentile Chunking...")
    percentile_chunker = SemanticPercentileChunker(
        min_tokens=150,
        max_tokens=800,
        percentile_threshold=25.0
    )
    
    try:
        semantic_chunks = percentile_chunker.chunk_document(document)
        print(f"   ✓ Generated {len(semantic_chunks)} semantic percentile chunks")
        if semantic_chunks:
            print(f"   First chunk preview: {semantic_chunks[0]['text'][:100]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        semantic_chunks = []
    
    # Test similarity cluster chunking
    print("\n2. Testing Similarity Cluster Chunking...")
    cluster_chunker = SimilarityClusterChunker(
        min_tokens=150,
        max_tokens=800,
        similarity_threshold=0.75
    )
    
    try:
        cluster_chunks = cluster_chunker.chunk_document(document)
        print(f"   ✓ Generated {len(cluster_chunks)} similarity cluster chunks")
        if cluster_chunks:
            print(f"   First chunk preview: {cluster_chunks[0]['text'][:100]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        cluster_chunks = []
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  Semantic Percentile: {len(semantic_chunks)} chunks")
    print(f"  Similarity Cluster: {len(cluster_chunks)} chunks")
    print("=" * 80)
    
    return semantic_chunks, cluster_chunks


if __name__ == "__main__":
    semantic_chunks, cluster_chunks = test_chunking_simple()
    
    print("\nNOTE: If you see 0 chunks, the embedding API is failing.")
    print("The chunkers will use fallback behavior with zero vectors.")
    print("This means chunks will be created based on sentence positions rather than semantic similarity.")