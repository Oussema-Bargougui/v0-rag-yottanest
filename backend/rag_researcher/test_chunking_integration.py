"""
Integration test for chunking in upload pipeline.

Tests the complete upload flow: extraction → cleaning → chunking
"""

import requests
import json
from pathlib import Path


def create_test_document():
    """Create a simple test document."""
    content = """
# Banking Regulations Overview

Banking regulations are critical for financial stability. The Basel III framework establishes comprehensive capital requirements for banks worldwide. These requirements ensure that institutions maintain adequate capital buffers to absorb losses during economic downturns. The framework also includes liquidity requirements and leverage ratios to strengthen the banking sector's resilience.

## Anti-Money Laundering

Anti-Money Laundering (AML) regulations require financial institutions to implement robust monitoring systems. These systems must detect suspicious transactions and report them to relevant authorities. The Financial Action Task Force (FATF) sets international standards for AML and Counter-Terrorist Financing (CTF) measures. Compliance with these standards is mandatory for banks operating in the global financial system.

## Know Your Customer

Know Your Customer (KYC) procedures are essential components of banking compliance. Banks must verify the identity of their clients and assess their risk profiles. This process involves collecting personal information, proof of address, and understanding the nature of the customer's business activities. Effective KYC procedures help prevent fraud and ensure regulatory compliance.

## Risk Management

Risk management in banking involves identifying, assessing, and mitigating various types of risks. Credit risk, market risk, and operational risk are the primary categories. Banks use sophisticated models and stress testing to evaluate their risk exposure. The risk management framework must be aligned with the institution's strategic objectives and regulatory requirements.
"""
    return content


def test_upload_with_chunking():
    """Test document upload with chunking integration."""
    
    # Create test document
    test_content = create_test_document()
    
    # Save test document
    test_file = Path("test_banking_doc.md")
    test_file.write_text(test_content, encoding='utf-8')
    
    print("=" * 80)
    print("Testing Chunking Integration in Upload Pipeline")
    print("=" * 80)
    
    # Upload document
    url = "http://localhost:8000/rag/upload"
    
    with open(test_file, 'rb') as f:
        files = {'files': ('test_banking_doc.md', f, 'text/markdown')}
        response = requests.post(url, files=files)
    
    print(f"\nUpload Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Upload successful!")
        print(f"  Batch ID: {result['batch_id']}")
        print(f"  Total Files: {result['total_files']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Failed: {result['failed']}")
        
        # Check chunking results
        for doc in result['documents']:
            print(f"\n  Document: {doc['filename']}")
            print(f"    Status: {doc['status']}")
            
            if 'chunking' in doc:
                chunking = doc['chunking']
                print(f"\n    Chunking Results:")
                
                if 'semantic_percentile' in chunking:
                    sem = chunking['semantic_percentile']
                    print(f"      Semantic Percentile:")
                    print(f"        Count: {sem['count']}")
                    print(f"        Path: {sem['path']}")
                    if 'preview' in sem and sem['preview']:
                        print(f"        Preview: {sem['preview'][0]['text'][:100]}...")
                
                if 'similarity_cluster' in chunking:
                    clust = chunking['similarity_cluster']
                    print(f"      Similarity Cluster:")
                    print(f"        Count: {clust['count']}")
                    print(f"        Path: {clust['path']}")
                    if 'preview' in clust and clust['preview']:
                        print(f"        Preview: {clust['preview'][0]['text'][:100]}...")
                
                if 'error' in chunking:
                    print(f"      Error: {chunking['error']}")
        
        # Save response
        output_file = Path("output/chunking/integration_test_response.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Full response saved to: {output_file}")
        
        # Verify storage
        if result['documents']:
            doc_id = result['documents'][0]['doc_id']
            chunks_dir = Path("storage/chunks") / doc_id
            if chunks_dir.exists():
                print(f"\n✓ Chunks directory created: {chunks_dir}")
                
                semantic_file = chunks_dir / "semantic_chunks.json"
                cluster_file = chunks_dir / "cluster_chunks.json"
                
                if semantic_file.exists():
                    with open(semantic_file, 'r') as f:
                        semantic_chunks = json.load(f)
                    print(f"  ✓ Semantic chunks file: {len(semantic_chunks)} chunks")
                
                if cluster_file.exists():
                    with open(cluster_file, 'r') as f:
                        cluster_chunks = json.load(f)
                    print(f"  ✓ Cluster chunks file: {len(cluster_chunks)} chunks")
            else:
                print(f"\n✗ Chunks directory not found: {chunks_dir}")
        
        print("\n" + "=" * 80)
        print("✓ Integration test completed!")
        print("=" * 80)
        
    else:
        print(f"\n✗ Upload failed: {response.status_code}")
        print(f"  Error: {response.text}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print(f"\n✓ Cleanup: Removed test file")


if __name__ == "__main__":
    try:
        test_upload_with_chunking()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()