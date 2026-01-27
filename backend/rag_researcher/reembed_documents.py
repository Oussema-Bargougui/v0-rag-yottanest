"""
Re-embed all documents from chunks.

This script loads chunks and re-embeds them, ensuring text is preserved.
This fixes old embeddings that don't have text field.
"""
import json
import logging
from pathlib import Path
from config import Config
from modules.embedder import DocumentEmbedder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Re-embed all documents from chunks."""
    
    # Initialize embedder
    embedder = DocumentEmbedder()
    
    # Get all chunk files (in chunks/ subdirectories)
    chunks_dir = Path(__file__).parent / "storage" / "chunks"
    chunk_files = list(chunks_dir.glob("**/*_chunks.json"))
    
    logger.info(f"Found {len(chunk_files)} chunk files")
    
    for chunk_file in chunk_files:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {chunk_file.relative_to(chunks_dir)}")
        logger.info(f"{'='*80}")
        
        # Extract doc_id from filename
        doc_id = chunk_file.stem.replace("_chunks", "")
        logger.info(f"Document ID: {doc_id}")
        
        # Re-embed
        try:
            result = embedder.embed_document(doc_id)
            logger.info(f"Embedded {result['embedding_count']} chunks")
            logger.info(f"Saved to: {result['embedding_path']}")
        except Exception as e:
            logger.error(f"Failed to embed {doc_id}: {str(e)}")
            continue
    
    logger.info(f"\n{'='*80}")
    logger.info(f"RE-EMBEDDING COMPLETE")
    logger.info(f"{'='*80}")

if __name__ == "__main__":
    main()