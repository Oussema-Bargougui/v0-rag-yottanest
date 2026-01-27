"""
Debug script to check embeddings file structure
"""
import json
from pathlib import Path
from config import Config
import sys

# Add backend/rag_researcher to path
sys.path.insert(0, str(Path(__file__).parent))

# List all embeddings files (absolute path)
embeddings_dir = Path(__file__).parent / "storage" / "embeddings"
embeddings_files = list(embeddings_dir.glob("*.json"))

print(f"Found {len(embeddings_files)} embeddings files")

for emb_file in embeddings_files:
    print(f"\n{'='*80}")
    print(f"File: {emb_file.name}")
    print(f"{'='*80}")
    
    with open(emb_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check structure
    print(f"\nTop-level keys: {list(data.keys())}")
    
    embeddings = data.get("embeddings", [])
    print(f"\nNumber of embeddings: {len(embeddings)}")
    
    if embeddings:
        first_emb = embeddings[0]
        print(f"\nFirst embedding keys: {list(first_emb.keys())}")
        print(f"Has 'id': {'id' in first_emb}")
        print(f"Has 'vector': {'vector' in first_emb}")
        print(f"Has 'text': {'text' in first_emb}")
        print(f"Has 'payload': {'payload' in first_emb}")
        
        if 'text' in first_emb:
            text = first_emb['text']
            print(f"\nText preview (first 200 chars): {text[:200]}...")
        
        if 'payload' in first_emb:
            payload = first_emb['payload']
            print(f"\nPayload keys: {list(payload.keys())}")
            print(f"Payload has 'text': {'text' in payload}")
            print(f"Payload has 'chunk_id': {'chunk_id' in payload}")
            
            # Show some payload fields
            for key in ['doc_id', 'document_name', 'chunk_index', 'strategy']:
                if key in payload:
                    print(f"  {key}: {payload[key]}")