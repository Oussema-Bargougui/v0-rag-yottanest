"""
Add text to old embeddings that don't have it.

This script reads chunks files and adds text to existing embeddings.
Then repopulates Qdrant with the fixed embeddings.
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

def load_chunks_with_text(doc_id: str) -> dict:
    """Load chunks file for a document."""
    # Try both naming conventions
    chunks_dir = Path(__file__).parent / "storage" / "chunks"
    
    # Try doc_id subdirectory
    possible_paths = [
        chunks_dir / doc_id / "semantic_chunks.json",
        chunks_dir / doc_id / "cluster_chunks.json",
        chunks_dir / f"{doc_id}_chunks.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    return None

def main():
    """Add text to old embeddings and repopulate Qdrant."""
    
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
        
        if has_text:
            # Already has text - just upsert
            try:
                result = vector_store.upsert_document(doc_id, embeddings)
                logger.info(f"Upserted {result['points_upserted']} points")
                total_points_upserted += result['points_upserted']
            except Exception as e:
                logger.error(f"Failed to upsert: {str(e)}")
            continue
        
        # Need to add text from chunks
        logger.info(f"Adding text from chunks file...")
        
        # Load chunks
        chunks_data = load_chunks_with_text(doc_id)
        if not chunks_data:
            logger.error(f"Could not load chunks for {doc_id}")
            continue
        
        # Create text map: chunk_id -> text
        chunks_list = chunks_data.get("chunks", [])
        text_map = {c.get("chunk_id"): c.get("text", "") for c in chunks_list}
        
        logger.info(f"Loaded {len(text_map)} chunk texts")
        
        # Add text to embeddings
        for emb in embeddings:
            chunk_id = emb.get("id")
            if chunk_id in text_map:
                emb["text"] = text_map[chunk_id]
            else:
                logger.warning(f"Text not found for chunk_id={chunk_id}")
                emb["text"] = ""
        
        # Upsert to Qdrant
        try:
            result = vector_store.upsert_document(doc_id, embeddings)
            logger.info(f"Upserted {result['points_upserted']} points in {result['batches']} batches")
            total_points_upserted += result['points_upserted']
        except Exception as e:
            logger.error(f"Failed to upsert: {str(e)}")
            continue
        
        # Optionally: save updated embeddings file
        updated_path = emb_file.with_name(f"{emb_file.stem}_updated.json")
        with open(updated_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved updated embeddings to: {updated_path}")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"FIX AND REPOPULATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total files processed: {len(embeddings_files)}")
    logger.info(f"Total points upserted: {total_points_upserted}")
    logger.info(f"Qdrant count: {vector_store.count_points()}")

if __name__ == "__main__":
    main()