"""
Test script for LLM generation layer.

Tests the full generation pipeline:
1. Context building
2. Prompt building
3. LLM generation
4. Answer formatting
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.retriever import Retriever
from modules.llm_generator import LLMGenerator
from modules.llm_client import LLMClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Test generation layer."""
    
    print("="*80)
    print("Testing LLM Generation Layer")
    print("="*80)
    
    # Step 1: Test LLM client connection
    print("\n[Step 1] Testing LLM client connection...")
    try:
        llm_client = LLMClient()
        if llm_client.check_connection():
            print("✅ LLM client connected successfully")
        else:
            print("❌ LLM client connection failed")
            return
    except Exception as e:
        print(f"❌ LLM client error: {str(e)}")
        return
    
    # Step 2: Initialize components
    print("\n[Step 2] Initializing generation components...")
    try:
        generator = LLMGenerator(llm_client=llm_client)
        print("✅ LLM generator initialized")
    except Exception as e:
        print(f"❌ Generator initialization failed: {str(e)}")
        return
    
    # Step 3: Test retriever
    print("\n[Step 3] Testing retriever...")
    try:
        retriever = Retriever()
        print("✅ Retriever initialized")
    except Exception as e:
        print(f"❌ Retriever initialization failed: {str(e)}")
        return
    
    # Step 4: Retrieve chunks
    query = "What are the financial risks mentioned in the documents?"
    print(f"\n[Step 4] Retrieving chunks for query: '{query}'...")
    
    try:
        chunks = retriever.retrieve(query)
        print(f"✅ Retrieved {len(chunks)} chunks")
        
        if not chunks:
            print("❌ No chunks retrieved. Cannot test generation.")
            return
        
        # Show first chunk
        print(f"\nFirst chunk preview:")
        print(f"  Chunk ID: {chunks[0].get('chunk_id')}")
        print(f"  Score: {chunks[0].get('rerank_score', chunks[0].get('score')):.4f}")
        print(f"  Text: {chunks[0].get('text', '')[:150]}...")
        
    except Exception as e:
        print(f"❌ Retrieval failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Generate answer
    print(f"\n[Step 5] Generating answer...")
    try:
        answer = generator.generate(query, chunks)
        print("✅ Answer generated successfully")
        
        # Display answer
        print("\n" + "="*80)
        print("GENERATED ANSWER")
        print("="*80)
        print(f"\nQuery: {answer.get('query')}")
        print(f"\nAnswer:\n{answer.get('answer')}")
        print(f"\nEvidence:\n{answer.get('evidence')}")
        print(f"\nLimitations:\n{answer.get('limitations')}")
        print(f"\nCitations: {answer.get('citations')}")
        print(f"\nChunks Used: {answer.get('chunks_count')}")
        print(f"Confidence: {answer.get('confidence')}")
        print(f"Model: {answer.get('model')}")
        
        # Display citation validation
        validation = answer.get('citation_validation', {})
        print(f"\nCitation Validation:")
        print(f"  Total: {validation.get('total_citations', 0)}")
        print(f"  Valid: {validation.get('valid_citations', 0)}")
        print(f"  Invalid: {validation.get('invalid_citations', 0)}")
        print(f"  Validation Rate: {validation.get('validation_rate', 0):.2%}")
        
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("✅ All tests passed!")
    print("="*80)

if __name__ == "__main__":
    main()