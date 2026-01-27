"""
Re-populate Qdrant with text in payload for all existing embeddings.

This script reads all existing embeddings files and upserts them to Qdrant
with text properly included in the payload.
"""
import json
import logging
from pathlib import Path
from config import Config
from modules.vector_store import VectorStore

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Repopulate Qdrant with all existing embeddings."""
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Get all embedding files
    embeddings_dir = Path(__file__).parent / "storage" / "embeddings"
    embeddings_files = list(embeddings_dir.glob("*.json"))
    
    logger.info(f"Found {len(embeddings_files)} embedding files")
    
    total_points_upserted = 0
    
    for emb_file in embeddings_files:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {emb_file.name}")
        logger.info(f"{'='*80}")
        
        # Load embeddings
        with open(emb_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc_id = data.get("doc_id")
        embeddings = data.get("embeddings", [])
        
        logger.info(f"Document ID: {doc_id}")
        logger.info(f"Number of embeddings: {len(embeddings)}")
        
        # Check if embeddings have text field
        has_text = any("text" in emb for emb in embeddings)
        logger.info(f"Embeddings have text field: {has_text}")
        
        if not has_text:
            logger.warning(f"No text field in embeddings - skipping {emb_file.name}")
            continue
        
        # Upsert to Qdrant
        try:
            result = vector_store.upsert_document(doc_id, embeddings)
            logger.info(f"Upserted {result['points_upserted']} points in {result['batches']} batches")
            total_points_upserted += result['points_upserted']
        except Exception as e:
            logger.error(f"Failed to upsert {emb_file.name}: {str(e)}")
            continue
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"REPOPULATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total files processed: {len(embeddings_files)}")
    logger.info(f"Total points upserted: {total_points_upserted}")
    logger.info(f"Qdrant count: {vector_store.count_points()}")

if __name__ == "__main__":
    main()