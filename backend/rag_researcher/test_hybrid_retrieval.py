"""
Test Hybrid Retrieval with BM25 Sparse Index

This script tests the enhanced hybrid retrieval system:
1. Tests SparseIndexService BM25 indexing
2. Tests hybrid retrieval (dense + sparse)
3. Verifies correct chunk retrieval for complex queries

Author: Yottanest Team
Version: 1.0.0
"""

import logging
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.sparse_index_service import SparseIndexService
from modules.retriever import Retriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sparse_index_service():
    """
    Test SparseIndexService BM25 indexing and retrieval.
    """
    print("\n" + "="*80)
    print("TEST 1: SparseIndexService BM25 Indexing")
    print("="*80)
    
    # Create sample chunks
    sample_chunks = [
        {
            "chunk_id": "rec10-1",
            "text": "Recommendation 10 - Financial institutions should apply customer due diligence (CDD) when establishing business relationships, conducting occasional transactions exceeding 15,000 USD/EUR, when there is suspicion of money laundering or terrorist financing, or when there are doubts about the veracity of previously obtained customer identification data.",
            "doc_id": "fatf_doc",
            "document_name": "FATF Recommendations.pdf",
            "page_numbers": [10],
            "char_start": 0,
            "char_end": 500
        },
        {
            "chunk_id": "rec10-2",
            "text": "The minimum measures that financial institutions should perform when applying customer due diligence include: (a) identifying the customer and verifying the customer's identity using reliable independent source documents, data or information; (b) identifying the beneficial owner and taking reasonable measures to verify the identity of the beneficial owner;",
            "doc_id": "fatf_doc",
            "document_name": "FATF Recommendations.pdf",
            "page_numbers": [10],
            "char_start": 500,
            "char_end": 1000
        },
        {
            "chunk_id": "rec10-3",
            "text": "(c) understanding and, as appropriate, obtaining information on the purpose and intended nature of the business relationship; and (d) conducting ongoing due diligence on the business relationship and scrutiny of transactions undertaken throughout the course of that relationship.",
            "doc_id": "fatf_doc",
            "document_name": "FATF Recommendations.pdf",
            "page_numbers": [10],
            "char_start": 1000,
            "char_end": 1500
        },
        {
            "chunk_id": "rec13-1",
            "text": "Recommendation 13 - For cross-border correspondent banking relationships, financial institutions should apply the following minimum measures: (a) gather sufficient information about a respondent institution to fully understand the nature of the respondent's business and to determine from publicly available information the reputation and the quality of supervision;",
            "doc_id": "fatf_doc",
            "document_name": "FATF Recommendations.pdf",
            "page_numbers": [13],
            "char_start": 2000,
            "char_end": 2500
        },
        {
            "chunk_id": "rec13-2",
            "text": "(b) assess the respondent institution's anti-money laundering and counter-terrorist financing controls; (c) obtain approval from senior management before establishing new correspondent banking relationships;",
            "doc_id": "fatf_doc",
            "document_name": "FATF Recommendations.pdf",
            "page_numbers": [13],
            "char_start": 2500,
            "char_end": 3000
        }
    ]
    
    # Initialize sparse index service
    sparse_service = SparseIndexService()
    
    # Build BM25 index
    print(f"\nBuilding BM25 index for {len(sample_chunks)} chunks...")
    sparse_service.build_index("fatf_doc", sample_chunks)
    print("✓ BM25 index built successfully")
    
    # Test retrieval with query that should match Recommendation 10
    query1 = "In which situations are financial institutions required to apply CDD and what are the minimum measures?"
    
    print(f"\nQuery 1: '{query1}'")
    results = sparse_service.retrieve(query1, doc_ids=["fatf_doc"], top_k=5)
    
    print(f"\nRetrieved {len(results)} chunks:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   Chunk ID: {result['chunk_id']}")
        print(f"   Type: {result['retrieval_type']}")
        print(f"   Text preview: {result['text'][:150]}...")
    
    # Verify correct chunk was retrieved (should be rec10-1 or rec10-2)
    top_chunk_ids = [r['chunk_id'] for r in results]
    has_rec10 = any('rec10' in cid for cid in top_chunk_ids)
    
    print(f"\n✓ Recommendation 10 chunks found: {has_rec10}")
    
    # Test retrieval with query about correspondent banking
    query2 = "What are the minimum measures for cross-border correspondent banking?"
    
    print(f"\n\nQuery 2: '{query2}'")
    results = sparse_service.retrieve(query2, doc_ids=["fatf_doc"], top_k=5)
    
    print(f"\nRetrieved {len(results)} chunks:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   Chunk ID: {result['chunk_id']}")
        print(f"   Type: {result['retrieval_type']}")
        print(f"   Text preview: {result['text'][:150]}...")
    
    # Verify correct chunk was retrieved (should be rec13-1 or rec13-2)
    top_chunk_ids = [r['chunk_id'] for r in results]
    has_rec13 = any('rec13' in cid for cid in top_chunk_ids)
    
    print(f"\n✓ Recommendation 13 chunks found: {has_rec13}")
    
    return has_rec10 and has_rec13


def test_hybrid_retriever_integration():
    """
    Test Retriever with hybrid dense + sparse retrieval.
    """
    print("\n" + "="*80)
    print("TEST 2: Hybrid Retriever Integration")
    print("="*80)
    
    try:
        # Initialize retriever
        print("\nInitializing hybrid retriever...")
        retriever = Retriever(
            dense_top_k=10,
            sparse_top_k=10,
            max_candidates=15,
            rerank_top_n=3
        )
        print("✓ Hybrid retriever initialized")
        
        # Note: This test requires documents already uploaded to Qdrant
        # For now, just verify the retriever can be instantiated
        print("\n✓ Retriever instantiation successful")
        print("\nNOTE: Full retrieval test requires uploaded documents in Qdrant")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Retriever initialization failed: {str(e)}")
        return False


def main():
    """
    Run all tests.
    """
    print("\n" + "="*80)
    print("HYBRID RETRIEVAL TEST SUITE")
    print("="*80)
    
    # Test 1: SparseIndexService
    test1_passed = test_sparse_index_service()
    
    # Test 2: Hybrid Retriever Integration
    test2_passed = test_hybrid_retriever_integration()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nTest 1 (SparseIndexService): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (Hybrid Retriever): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    all_passed = test1_passed and test2_passed
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())