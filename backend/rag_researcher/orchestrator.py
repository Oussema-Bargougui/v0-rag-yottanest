#!/usr/bin/env python3
"""
RAG Pipeline Orchestrator

A clean, independent orchestrator that manages the entire RAG pipeline workflow.
Handles scenario detection, component initialization, and provides detailed step-by-step output.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import pipeline components
from modules.data_loader import DataLoader
from modules.text_cleaner import TextCleaner
from modules.chunker import TextChunker
from modules.embedder import TextEmbedder
from modules.vector_store import VectorStore
from modules.retriever import Retriever

class RAGOrchestrator:
    """
    Main orchestrator for the RAG pipeline.
    Handles component initialization, scenario detection, and workflow management.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the RAG orchestrator.
        
        Args:
            base_dir: Base directory for the RAG researcher (defaults to current directory)
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir / "input"
        self.output_dir = self.base_dir / "output"
        self.vector_db_path = self.base_dir / "output" / "vector_store.pkl"
        
        # Ensure directories exist
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.vector_db_path.parent.mkdir(exist_ok=True)
        
        # Initialize components
        self.components = {}
        self.logger = self._setup_logging()
        
        # Component references for easier access
        self.data_loader = None
        self.text_cleaner = None
        self.chunker = None
        self.embedder = None
        self.vector_store = None
        self.retriever = None
        
        print("\n" + "="*60)
        print("🚀 RAG PIPELINE ORCHESTRATOR INITIALIZED")
        print("="*60)
        print(f"📁 Base Directory: {self.base_dir}")
        print(f"📥 Input Directory: {self.input_dir}")
        print(f"📤 Output Directory: {self.output_dir}")
        print(f"🗄️  Vector DB Path: {self.vector_db_path}")
        print("="*60 + "\n")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('RAGOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_components(self):
        """
        Load and initialize all RAG pipeline components.
        """
        print("\n🔧 STEP 1: LOADING PIPELINE COMPONENTS")
        print("-" * 50)
        
        try:
            # Initialize Data Loader
            print("📖 Loading Data Loader...")
            self.data_loader = DataLoader()
            self.components['data_loader'] = self.data_loader
            print("   ✅ Data Loader initialized")
            
            # Initialize Text Cleaner
            print("🧹 Loading Text Cleaner...")
            self.text_cleaner = TextCleaner()
            self.components['text_cleaner'] = self.text_cleaner
            print("   ✅ Text Cleaner initialized")
            
            # Initialize Chunker
            print("✂️  Loading Text Chunker...")
            self.chunker = TextChunker(chunk_size=500, overlap_size=50)
            self.components['chunker'] = self.chunker
            print("   ✅ Text Chunker initialized (chunk_size=500, overlap=50)")
            
            # Initialize Embedder
            print("🧠 Loading Text Embedder...")
            self.embedder = TextEmbedder(
                model_provider="nomic",
                model_name="nomic-embed-text:latest"
            )
            self.components['embedder'] = self.embedder
            print("   ✅ Text Embedder initialized (nomic-embed-text:latest)")
            
            # Initialize Vector Store
            print("🗄️  Loading Vector Store...")
            if self.vector_db_path.exists():
                print("   📊 Loading existing vector database...")
                self.vector_store = VectorStore.load(str(self.vector_db_path))
                print(f"   ✅ Loaded existing vector store with {len(self.vector_store.documents)} documents")
            else:
                print("   🆕 Creating new vector store...")
                self.vector_store = VectorStore(
                    distance_metric="cosine"
                )
                print("   ✅ New vector store initialized")
            self.components['vector_store'] = self.vector_store
            
            # Initialize Retriever
            print("🔍 Loading Retriever...")
            self.retriever = Retriever(
                vector_store=self.vector_store,
                embedder=self.embedder
            )
            self.components['retriever'] = self.retriever
            print("   ✅ Retriever initialized")
            
            print("\n✅ ALL COMPONENTS LOADED SUCCESSFULLY!")
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Error loading components: {str(e)}")
            self.logger.error(f"Component loading failed: {str(e)}")
            raise
    
    def detect_scenario(self) -> str:
        """
        Detect the current scenario based on input data and vector store state.
        
        Returns:
            str: Scenario type ('process_documents', 'query_mode', 'no_data')
        """
        print("\n🔍 STEP 2: SCENARIO DETECTION")
        print("-" * 50)
        
        # Check for input files
        input_files = self._get_input_files()
        has_input = len(input_files) > 0
        
        # Check for existing vector store
        has_vector_db = self.vector_db_path.exists() and self.vector_db_path.stat().st_size > 0
        
        print(f"📥 Input files found: {len(input_files)}")
        if input_files:
            for file in input_files:
                print(f"   - {file.name}")
        
        print(f"🗄️  Existing vector database: {'Yes' if has_vector_db else 'No'}")
        
        if has_input:
            scenario = "process_documents"
            print("\n📋 SCENARIO: DOCUMENT PROCESSING MODE")
            print("   → Will process input documents and update vector store")
        elif has_vector_db:
            scenario = "query_mode"
            print("\n📋 SCENARIO: QUERY MODE")
            print("   → Ready for queries against existing vector database")
        else:
            scenario = "no_data"
            print("\n📋 SCENARIO: NO DATA AVAILABLE")
            print("   → No input files and no existing vector database")
        
        print("-" * 50)
        return scenario
    
    def _get_input_files(self) -> List[Path]:
        """Get list of supported input files."""
        supported_extensions = {'.txt', '.pdf', '.docx', '.md'}
        input_files = []
        
        if self.input_dir.exists():
            for file_path in self.input_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    input_files.append(file_path)
        
        return input_files
    
    def run_document_processing(self):
        """Process documents and create/update vector store"""
        print("\n📄 STEP 3: DOCUMENT PROCESSING")
        print("-" * 50)
        
        try:
            # Load documents
            print("📂 Loading documents...")
            documents = self.data_loader.load_all_files()
            print(f"   ✅ Loaded {len(documents)} documents")
            
            if not documents:
                print("   ⚠️  No documents found to process")
                return {'success': False, 'error': 'No documents found'}
            
            # Clean documents
            print("🧹 Cleaning documents...")
            cleaned_docs = self.text_cleaner.clean_documents(documents)
            print(f"   ✅ Cleaned {len(cleaned_docs)} documents")
            
            # Chunk documents
            print("✂️  Chunking documents...")
            all_chunks = []
            for doc in cleaned_docs:
                chunks = self.chunker.chunk_text(doc['content'])
                for i, chunk in enumerate(chunks):
                    all_chunks.append({
                        'text': chunk,
                        'filename': doc['filename'],
                        'chunk_id': i,
                        'metadata': doc.get('metadata', {})
                    })
            print(f"   ✅ Generated {len(all_chunks)} chunks")
            
            # Generate embeddings
            print("🔢 Generating embeddings...")
            embedded_chunks = self.embedder.embed_documents(all_chunks)
            print(f"   ✅ Generated {len(embedded_chunks)} embeddings")
            
            # Store in vector database
            print("💾 Updating vector store...")
            self.vector_store.add_documents(embedded_chunks)
            print(f"   ✅ Updated vector store with {len(embedded_chunks)} documents")
            
            # Save vector store
            print("💾 Saving vector store...")
            self.vector_store.save(str(self.vector_db_path))
            print(f"   ✅ Saved to {self.vector_db_path}")
            
            # Clean up input files
            print("🧹 Cleaning up input files...")
            for file_path in self.input_dir.glob('*'):
                if file_path.is_file():
                    file_path.unlink()
            print("   ✅ Input files cleaned up")
            
            print("\n✅ DOCUMENT PROCESSING COMPLETED SUCCESSFULLY!")
            
            return {
                'success': True,
                'documents_processed': len(documents),
                'chunks_generated': len(all_chunks),
                'embeddings_created': len(embedded_chunks)
            }
            
        except Exception as e:
            print(f"   ❌ Error during processing: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_results_as_markdown(self, query: str, results: List[Dict[str, Any]], timestamp: str, top_k: int) -> str:
        """Format retrieval results as markdown"""
        markdown = f"# Query Results\n\n"
        markdown += f"**Query:** {query}\n\n"
        markdown += f"**Timestamp:** {timestamp}\n\n"
        markdown += f"**Top K:** {top_k}\n\n"
        markdown += f"**Results Found:** {len(results)}\n\n"
        markdown += "---\n\n"
        
        for i, result in enumerate(results, 1):
            # Extract key information
            score = result.get('similarity_score', result.get('score', 0))
            content = result.get('text', result.get('content', 'N/A'))
            filename = result.get('filename', result.get('source', 'Unknown'))
            chunk_id = result.get('chunk_id', 'N/A')
            
            # Add scores if available
            scores_info = f"**Similarity Score:** {score:.4f}"
            if 'semantic_score' in result:
                scores_info += f" | **Semantic:** {result['semantic_score']:.4f}"
            if 'keyword_score' in result:
                scores_info += f" | **Keyword:** {result['keyword_score']:.4f}"
            if 'rerank_score' in result:
                scores_info += f" | **Rerank:** {result['rerank_score']:.4f}"
            
            markdown += f"## Result {i}\n\n"
            markdown += f"{scores_info}\n\n"
            markdown += f"**Source:** {filename}\n\n"
            markdown += f"**Chunk ID:** {chunk_id}\n\n"
            markdown += f"**Content:**\n\n"
            markdown += f"```\n{content}\n```\n\n"
            
            # Add metadata if available
            if 'metadata' in result and result['metadata']:
                markdown += f"**Metadata:**\n\n"
                for key, value in result['metadata'].items():
                    markdown += f"- **{key}:** {value}\n"
                markdown += "\n"
            
            markdown += "---\n\n"
        
        return markdown
    
    def run_query_processing(self, query: str, top_k: int = 5):
        """Process query and retrieve relevant documents"""
        print(f"\n🔍 STEP 3: QUERY PROCESSING")
        print("-" * 50)
        print(f"📝 Query: '{query}'")
        print(f"🎯 Retrieving top {top_k} results...")
        
        try:
            # Load existing vector database if it exists
            if self.vector_db_path.exists():
                print("📊 Loading vector database...")
                self.vector_store = VectorStore.load(str(self.vector_db_path))
                # Update retriever's vector store reference
                self.retriever.vector_store = self.vector_store
                print("   ✅ Vector database loaded")
            else:
                print("   ❌ No vector database found")
                return {
                    "success": False,
                    "error": "No vector database found",
                    "results": []
                }
            
            # Embed the query
            print("🧠 Embedding query...")
            query_embedding = self.embedder.embed_text(query)
            print("   ✅ Query embedded")
            
            # Search vector database
            print("🔍 Searching vector database...")
            results = self.retriever.retrieve(
                query=query,
                top_k=top_k
            )
            
            if results:
                print(f"   ✅ Found {len(results)} relevant documents")
                
                # Display results like intelligent pipeline
                print(f"\n✅ Found {len(results)} relevant results:\n")
                for i, result in enumerate(results, 1):
                    score = result.get('similarity_score', result.get('score', 0))
                    content = result.get('text', result.get('content', 'N/A'))
                    filename = result.get('filename', result.get('source', 'Unknown'))
                    
                    print(f"📄 Result {i} (Score: {score:.4f})")
                    print(f"   File: {filename}")
                    print(f"   Content: {str(content)[:200]}...")
                    print()
                
                # Save results in markdown format
                results_dir = self.output_dir / "retriever"
                results_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                results_file = results_dir / f"query_results_{timestamp}.md"
                
                # Format results as markdown
                markdown_content = self._format_results_as_markdown(query, results, timestamp, top_k)
                
                with open(results_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                print(f"📁 Detailed results saved in: {results_file}")
                
                return {
                    "success": True,
                    "query": query,
                    "results_count": len(results),
                    "results": results,
                    "saved_to": str(results_file)
                }
            else:
                print("   ❌ No relevant documents found for your query.")
                return {
                    "success": True,
                    "query": query,
                    "results_count": 0,
                    "results": [],
                    "message": "No relevant documents found"
                }
                
        except Exception as e:
            print(f"   ❌ Error during retrieval: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def run_intelligent_pipeline(self, query: Optional[str] = None, top_k: int = 5):
        """
        Main intelligent pipeline that:
        1. Detects current scenario
        2. Processes documents if needed
        3. Retrieves results if query provided
        """
        try:
            # Step 1: Load all components
            self.load_components()
            
            # Step 2: Detect scenario
            scenario = self.detect_scenario()
            self.logger.info(f"Detected scenario: {scenario}")
            
            if scenario == "no_data":
                self.logger.error("No input files and no vector database found!")
                print("❌ Error: No documents to process and no existing vector database.")
                print("Please add documents to the 'input' folder first.")
                return None
            
            # Handle processing scenarios
            if scenario in ["process_documents"]:
                self.logger.info("Processing documents...")
                print(f"📁 Found input files. Processing documents...")
                
                try:
                    # Process documents
                    result = self.run_document_processing()
                    if result['success']:
                        print("✅ Document processing completed successfully!")
                        # Update scenario after processing
                        scenario = "query_ready"
                    else:
                        print(f"❌ Error during processing: {result.get('error', 'Unknown error')}")
                        return None
                        
                except Exception as e:
                    self.logger.error(f"Error during processing: {e}")
                    print(f"❌ Error during processing: {e}")
                    return None
            
            # Handle query if provided
            if query and scenario in ["query_mode", "query_ready"]:
                self.logger.info(f"Retrieving results for query: '{query}'")
                print(f"🔍 Searching for: '{query}'")
                
                try:
                    # Retrieve results
                    results = self.run_query_processing(query, top_k=top_k)
                    
                    if results.get('success') and results.get('results'):
                        print(f"\n🎯 Retrieved {len(results['results'])} results successfully!")
                        return results['results']
                    elif results.get('success') and not results.get('results'):
                        print("❌ No relevant results found for your query.")
                        return []
                    else:
                        print(f"❌ Error during retrieval: {results.get('error', 'Unknown error')}")
                        return None
                        
                except Exception as e:
                    self.logger.error(f"Error during retrieval: {e}")
                    print(f"❌ Error during retrieval: {e}")
                    return None
            
            elif query:
                print("⚠️  Query provided but no vector database available after processing.")
                return None
            
            else:
                print("✅ Processing completed. Provide a query to search the documents.")
                return "processed"
                
        except Exception as e:
            self.logger.error(f"Orchestrator execution failed: {str(e)}")
            print(f"❌ Orchestrator execution failed: {str(e)}")
            return None

def main():
    """
    Main entry point for the orchestrator
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Pipeline Orchestrator - Step-by-Step Execution")
    parser.add_argument("--query", "-q", type=str, help="Query to search for")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to return")
    parser.add_argument("--input-dir", type=str, default="input", help="Input directory path")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory path")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = RAGOrchestrator(
        base_dir=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Run intelligent pipeline
    print("🚀 Starting RAG Pipeline Orchestrator...")
    print(f"   Input Directory: {args.input_dir}")
    print(f"   Output Directory: {args.output_dir}")
    if args.query:
        print(f"   Query: '{args.query}'")
        print(f"   Top-K Results: {args.top_k}")
    print()
    
    results = orchestrator.run_intelligent_pipeline(
        query=args.query,
        top_k=args.top_k
    )
    
    if results == "processed":
        print("\n💡 Tip: Run again with --query 'your question' to search the processed documents.")
    elif results:
        print(f"\n🎯 Retrieved {len(results)} results successfully!")
        print("📁 Detailed results saved in the output/retriever folder.")
    
    print(f"\n🏁 FINAL RESULT: {{'scenario': 'completed', 'success': {results is not None}, 'results': {results if isinstance(results, list) else []}}}")

if __name__ == "__main__":
    main()