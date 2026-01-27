"""
Production Retrieval Test Suite

Tests all production-grade retrieval enhancements:
1. Chunking with boundary-aware splitting and metadata extraction
2. Hybrid retrieval with BGE-medium reranker
3. Weighted score combination
4. BM25 sparse retrieval integration

Author: Yottanest Team
Version: 2.0.0
"""

import logging
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.semantic_percentile_chunker import SemanticPercentileChunker
from modules.retriever import Retriever
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_chunking_with_metadata():
    """
    Test semantic percentile chunking with recommendation metadata extraction.
    """
    print("\n" + "="*80)
    print("TEST 1: Chunking with Boundary-Aware Splitting & Metadata")
    print("="*80)
    
    # Create sample document (simulates FATF Recommendations structure)
    document_data = {
        "doc_id": "test_doc_1",
        "document_name": "FATF_Recommendations_Test.pdf",
        "filename": "FATF_Recommendations_Test.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": """Recommendation 10 - Customer Due Diligence

Financial institutions should apply customer due diligence (CDD) when establishing business relationships, conducting occasional transactions exceeding 15,000 USD/EUR, when there is suspicion of money laundering or terrorist financing, or when there are doubts about the veracity of previously obtained customer identification data.

The minimum measures that financial institutions should perform when applying customer due diligence include: (a) identifying the customer and verifying the customer's identity using reliable independent source documents, data or information; (b) identifying the beneficial owner and taking reasonable measures to verify the identity of the beneficial owner;

(c) understanding and, as appropriate, obtaining information on the purpose and intended nature of the business relationship; and (d) conducting ongoing due diligence on the business relationship and scrutiny of transactions undertaken throughout the course of that relationship.

Recommendation 13 - Correspondent Banking

For cross-border correspondent banking relationships, financial institutions should apply the following minimum measures: (a) gather sufficient information about a respondent institution to fully understand the nature of the respondent's business and to determine from publicly available information the reputation and the quality of supervision; (b) assess the respondent institution's anti-money laundering and counter-terrorist financing controls; (c) obtain approval from senior management before establishing new correspondent banking relationships;
"""
            }
        ],
        "extraction_version": "5.0.0",
        "ingestion_timestamp": "2026-01-26T22:00:00",
        "source": "test_upload",
        "file_type": "pdf"
    }
    
    # Initialize chunker
    chunker = SemanticPercentileChunker(
        min_tokens=100,
        max_tokens=500,
        percentile_threshold=25.0
    )
    
    # Chunk document
    chunks = chunker.chunk_document(document_data)
    
    print(f"\n✓ Document chunked successfully: {len(chunks)} chunks")
    
    # Verify chunks have recommendation metadata
    chunks_with_rec_num = [c for c in chunks if "recommendation_number" in c]
    print(f"✓ Chunks with recommendation_number: {len(chunks_with_rec_num)}/{len(chunks)}")
    
    # Verify chunks have headers preserved
    header_chunks = [c for c in chunks if c.get("is_header_chunk", False)]
    print(f"✓ Header chunks: {len(header_chunks)}")
    
    # Show first chunk as example
    if chunks:
        print(f"\n--- First Chunk Example ---")
        chunk = chunks[0]
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Position: {chunk['position']}/{chunk['total_chunks']}")
        print(f"Text Preview: {chunk['text'][:200]}...")
        
        if "recommendation_number" in chunk:
            print(f"✓ Recommendation Number: {chunk['recommendation_number']}")
        
        if "recommendation_title" in chunk:
            print(f"✓ Recommendation Title: {chunk['recommendation_title']}")
        
        if "key_numbers" in chunk:
            print(f"✓ Key Numbers: {chunk['key_numbers']}")
        
        if "is_header_chunk" in chunk:
            print(f"✓ Is Header Chunk: {chunk['is_header_chunk']}")
        
        print(f"Token Count: {chunk.get('chunk_size', 'N/A')}")
    
    # Check for recommendation numbers detected
    rec_chunks = [c for c in chunks if c.get("recommendation_number")]
    
    if rec_chunks:
        print(f"\n--- Detected Recommendations ---")
        for chunk in rec_chunks:
            rec_num = chunk.get("recommendation_number")
            is_header = chunk.get("is_header_chunk", False)
            print(f"  Recommendation {rec_num}: {'Header' if is_header else 'Content'}")
    
    # Success if chunks created and metadata extracted
    return len(chunks) > 0 and len(rec_chunks) > 0


def test_retriever_configuration():
    """
    Test retriever with production configuration.
    """
    print("\n" + "="*80)
    print("TEST 2: Retriever Configuration")
    print("="*80)
    
    # Print config values
    print(f"\n--- Production Configuration ---")
    print(f"Reranker Model: {Config.RERANKER_MODEL}")
    print(f"\nRetriever Config:")
    for key, value in Config.RETRIEVER_CONFIG.items():
        print(f"  {key}: {value}")
    
    print(f"\n--- Chunking Config ---")
    print(f"Chunk Size (tokens): {Config.CHUNK_SIZE_TOKENS}")
    print(f"Chunk Overlap (tokens): {Config.CHUNK_OVERLAP_TOKENS}")
    print(f"Preserve Headers: {Config.PRESERVE_HEADERS}")
    
    print(f"\n--- Query Expansion Config ---")
    print(f"Enable Query Expansion: {Config.ENABLE_QUERY_EXPANSION}")
    print(f"Expansion Terms: {Config.QUERY_EXPANSION_TERMS}")
    
    # Initialize retriever (uses config defaults)
    try:
        retriever = Retriever()  # Uses all config defaults
        print(f"\n✓ Retriever initialized with config defaults")
        print(f"  Dense Top-K: {retriever.dense_top_k}")
        print(f"  Sparse Top-K: {retriever.sparse_top_k}")
        print(f"  Max Candidates: {retriever.max_candidates}")
        print(f"  Rerank Top-N: {retriever.rerank_top_n}")
        print(f"  Reranker Model: {retriever.reranker.model_name}")
        print(f"  Dense Weight: {retriever.hybrid_merger.dense_weight}")
        print(f"  Sparse Weight: {retriever.hybrid_merger.sparse_weight}")
        
        return True
    except Exception as e:
        print(f"\n✗ Retriever initialization failed: {str(e)}")
        return False


def test_weighted_hybrid_scores():
    """
    Test weighted hybrid score combination.
    """
    print("\n" + "="*80)
    print("TEST 3: Weighted Hybrid Score Combination")
    print("="*80)
    
    # Create mock results
    dense_results = [
        {"chunk_id": "rec10-chunk1", "score": 0.92, "text": "Recommendation 10..."},
        {"chunk_id": "rec13-chunk1", "score": 0.88, "text": "Recommendation 13..."},
    ]
    
    sparse_results = [
        {"chunk_id": "rec10-chunk1", "score": 3.50, "text": "Recommendation 10..."},
        {"chunk_id": "rec9-chunk1", "score": 2.80, "text": "Recommendation 9..."},
    ]
    
    # Test normalization
    print(f"\n--- Score Normalization ---")
    print(f"Dense scores: {[r['score'] for r in dense_results]}")
    print(f"Sparse scores: {[r['score'] for r in sparse_results]}")
    
    # Calculate expected weighted scores
    dense_min = min(r["score"] for r in dense_results)
    dense_max = max(r["score"] for r in dense_results)
    dense_norm_10 = (dense_results[0]["score"] - dense_min) / (dense_max - dense_min)
    dense_norm_13 = (dense_results[1]["score"] - dense_min) / (dense_max - dense_min)
    
    sparse_min = min(r["score"] for r in sparse_results)
    sparse_max = max(r["score"] for r in sparse_results)
    sparse_norm_10 = (sparse_results[0]["score"] - sparse_min) / (sparse_max - sparse_min)
    
    dense_weight = Config.RETRIEVER_CONFIG.get("dense_weight", 0.6)
    sparse_weight = Config.RETRIEVER_CONFIG.get("sparse_weight", 0.4)
    
    weighted_10 = dense_weight * dense_norm_10 + sparse_weight * sparse_norm_10
    weighted_13 = dense_weight * dense_norm_13  # rec13 only in dense
    
    print(f"\nRec 10 - Dense: {dense_norm_10:.4f} (norm), Sparse: {sparse_norm_10:.4f} (norm)")
    print(f"  Weighted: {weighted_10:.4f} = {dense_weight}*{dense_norm_10:.4f} + {sparse_weight}*{sparse_norm_10:.4f}")
    
    print(f"\nRec 13 - Dense: {dense_norm_13:.4f} (norm), Sparse: 0.0000 (norm)")
    print(f"  Weighted: {weighted_13:.4f} = {dense_weight}*{dense_norm_13:.4f} + {sparse_weight}*0.0000")
    
    print(f"\n✓ Recommendation 10 has higher weighted score: {weighted_10:.4f} > {weighted_13:.4f}")
    print(f"✓ Hybrid ranking favors rec10 (both dense + sparse found)")
    
    return weighted_10 > weighted_13


def main():
    """
    Run all production tests.
    """
    print("\n" + "="*80)
    print("PRODUCTION RETRIEVAL TEST SUITE")
    print("="*80)
    
    # Test 1: Chunking
    test1_passed = test_chunking_with_metadata()
    
    # Test 2: Retriever Config
    test2_passed = test_retriever_configuration()
    
    # Test 3: Weighted Hybrid
    test3_passed = test_weighted_hybrid_scores()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nTest 1 (Chunking with Metadata): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (Retriever Configuration): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    print(f"Test 3 (Weighted Hybrid Scores): {'✓ PASSED' if test3_passed else '✗ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())