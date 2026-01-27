#!/usr/bin/env python3
"""
LangChain-Based RAG-First Production Data Loader

This module uses LangChain loaders (Unstructured-based) for document extraction
with RAG-FIRST design.

Key Features:
- Extracts clean, compact, linear text only (no layout blocks, no bbox)
- Table handling: real tables only, converted to inline text
- Image handling: inline injection with LLM-generated captions and descriptions
- OCR fallback for scanned PDFs
- Batch ingestion support
- Multi-format support (PDF, DOCX, TXT, MD)

Author: Yottanest Team
Version: 5.0.0 - LangChain-First Production
"""

import os
import uuid
import logging
import base64
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import LangChain loaders
try:
    from langchain_community.document_loaders import (
        UnstructuredPDFLoader,
        UnstructuredWordDocumentLoader,
        UnstructuredMarkdownLoader,
        TextLoader
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available. Install with: pip install langchain-community unstructured")

# Import PIL for image processing
try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not available. Install with: pip install Pillow")

# Import PyMuPDF for image extraction
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available. Install with: pip install PyMuPDF")


class LangChainRAGLoader:
    """
    LangChain-first production data loader for RAG systems.
    
    This class provides document processing with RAG-optimized output:
    - Clean, linear text per page (no layout blocks, no bbox)
    - Inline table text representations
    - Inline image captions with LLM descriptions
    - OCR fallback for scanned documents
    """
    
    # Configuration constants
    MIN_IMAGE_SIZE = 100  # Min width/height for image processing (px)
    MIN_IMAGE_SIZE_FOR_LLM = 150  # Min size for LLM captioning (px)
    IMAGES_PER_PAGE_LIMIT = 2  # Limit images per page to avoid over-processing
    
    def __init__(self):
        """Initialize LangChain RAG loader."""
        # Ensure storage directories exist
        self.storage_path = Config.get_storage_path()
        self.images_path = self.storage_path / "images"
        self.images_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("LangChainRAGLoader initialized (LangChain-First Production v5.0)")
        logger.info(f"Storage path: {self.storage_path}")
        logger.info(f"Images path: {self.images_path}")
        
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required. Install with: pip install langchain-community unstructured")
    
    def get_loader(self, file_path: str):
        """
        Get appropriate LangChain loader based on file type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            LangChain document loader instance
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            logger.info(f"Using UnstructuredPDFLoader with hi_res strategy for {file_path}")
            return UnstructuredPDFLoader(
                file_path, 
                strategy="hi_res",
                extract_images_in_pdf=True,
                infer_table_structure=True,
                mode="elements"
            )
        elif ext == '.docx':
            logger.info(f"Using UnstructuredWordDocumentLoader for {file_path}")
            return UnstructuredWordDocumentLoader(file_path)
        elif ext in ['.txt', '.text']:
            logger.info(f"Using TextLoader for {file_path}")
            return TextLoader(file_path)
        elif ext in ['.md', '.markdown']:
            logger.info(f"Using UnstructuredMarkdownLoader for {file_path}")
            return UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def process_uploaded_file(self, 
                         content: bytes, 
                         filename: str,
                         file_type: str = 'pdf') -> Optional[Dict[str, Any]]:
        """
        Process an uploaded file using LangChain loaders.
        
        Args:
            content: File content as bytes
            filename: Original filename
            file_type: File type ('pdf', 'docx', 'txt', 'md')
            
        Returns:
            RAG-ready document dictionary with clean text, pages, and full_text
        """
        try:
            # Sanitize filename
            try:
                filename = str(filename)
                filename = filename.split(";")[0].strip()
                logger.info(f"Processing uploaded file: {filename} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"Filename sanitization failed: {str(e)}")
                filename = "unknown_file"
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Use LangChain loader
                loader = self.get_loader(tmp_path)
                docs = loader.load()
                
                logger.info(f"LangChain extracted {len(docs)} document elements")
                
                # Process documents and build pages
                pages = self._process_documents(docs, doc_id, filename, tmp_path)
                
                # Build full text
                full_text = '\n\n'.join(page['text'] for page in pages)
                
                # Build result
                result = {
                    'doc_id': doc_id,
                    'filename': filename,
                    'file_type': file_type,
                    'pages': pages,
                    'metadata': {
                        'source': 'upload',
                        'file_type': file_type,
                        'created_at': datetime.now().isoformat(),
                        'original_filename': filename,
                        'file_size': len(content)
                    },
                    'full_text': full_text
                }
                
                logger.info(f"Successfully processed {filename}: {len(pages)} pages, {len(full_text)} characters")
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return None
    
    def _process_documents(self, 
                       docs: List[Any], 
                       doc_id: str,
                       filename: str,
                       file_path: str) -> List[Dict[str, Any]]:
        """
        Process LangChain documents and build pages with RAG-first format.
        
        Args:
            docs: List of LangChain Document objects
            doc_id: Document ID
            filename: Original filename
            file_path: Path to file (for image extraction)
            
        Returns:
            List of page dictionaries with RAG-first format
        """
        pages = []
        current_page_text = ""
        current_page_number = 1
        
        for doc in docs:
            try:
                # Get page content
                page_content = doc.page_content
                metadata = doc.metadata
                
                # Determine page number
                page_num = metadata.get('page_number', current_page_number)
                
                # Check if this is a new page
                if page_num != current_page_number and current_page_text.strip():
                    # Save previous page
                    pages.append({
                        'page_number': current_page_number,
                        'text': current_page_text.strip(),
                        'metadata': {
                            'has_tables': 'TABLE' in current_page_text,
                            'has_images': 'IMAGE' in current_page_text
                        }
                    })
                    current_page_text = ""
                    current_page_number = page_num
                
                # Process element based on type
                element_type = metadata.get('category', '')
                
                if element_type == 'Table':
                    # Table - convert to inline text
                    table_text = self._process_table_element(page_content)
                    current_page_text += f"\n\n{table_text}"
                elif element_type == 'Image':
                    # Image - extract and generate caption/description
                    image_text = self._process_image_element(
                        page_content, 
                        metadata, 
                        doc_id, 
                        page_num,
                        file_path
                    )
                    if image_text:
                        current_page_text += f"\n\n{image_text}"
                else:
                    # Regular text - clean and merge
                    clean_text = self._clean_text(page_content)
                    current_page_text += f" {clean_text}"
                
            except Exception as e:
                logger.warning(f"Error processing document element: {str(e)}")
                continue
        
        # Don't forget the last page
        if current_page_text.strip():
            pages.append({
                'page_number': current_page_number,
                'text': current_page_text.strip(),
                'metadata': {
                    'has_tables': 'TABLE' in current_page_text,
                    'has_images': 'IMAGE' in current_page_text
                }
            })
        
        # If no pages were created, create a single page
        if not pages:
            logger.warning("No pages created from documents, creating single page")
            pages.append({
                'page_number': 1,
                'text': '',
                'metadata': {
                    'has_tables': False,
                    'has_images': False
                }
            })
        
        return pages
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for RAG consumption.
        
        Args:
            text: Raw text
            
        Returns:
            Clean, merged text string
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Fix hyphenation
        text = text.replace(' - ', '-')
        
        return text.strip()
    
    def _process_table_element(self, table_content: str) -> str:
        """
        Process table element and convert to inline text format.
        
        Args:
            table_content: Table content from LangChain
            
        Returns:
            Table as inline text string
        """
        lines = table_content.strip().split('\n')
        
        if not lines:
            return ""
        
        # Build table text
        result = ["TABLE"]
        
        # First line is typically headers
        if lines:
            headers = ' | '.join(line.strip() for line in lines[:1])
            result.append(f"Columns: {headers}")
        
        # Remaining lines are rows
        for line in lines[1:]:
            if line.strip():
                row_text = ' | '.join(cell.strip() for cell in line.split('|'))
                result.append(row_text)
        
        return '\n'.join(result)
    
    def _process_image_element(self,
                            image_content: str,
                            metadata: Dict[str, Any],
                            doc_id: str,
                            page_num: int,
                            file_path: str) -> Optional[str]:
        """
        Process image element with LLM captioning and description.
        
        Args:
            image_content: Image content/caption from LangChain
            metadata: Image metadata
            doc_id: Document ID
            page_num: Page number
            file_path: Path to file for image extraction
            
        Returns:
            Inline text with image caption and description
        """
        try:
            # Extract image from PDF if available
            image_data = self._extract_image_from_pdf(file_path, page_num)
            
            if not image_data:
                logger.info(f"No image data extracted for page {page_num}")
                return None
            
            # Check image size
            if PIL_AVAILABLE:
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                
                if width < self.MIN_IMAGE_SIZE or height < self.MIN_IMAGE_SIZE:
                    logger.info(f"Skipping small image: {width}x{height}")
                    return None
            else:
                width, height = 0, 0
            
            # Save image
            image_id = f"{doc_id}_page_{page_num}_img_{uuid.uuid4().hex[:8]}"
            image_filename = f"{image_id}.png"
            image_path = self.images_path / image_filename
            
            if PIL_AVAILABLE:
                image.save(image_path, "PNG")
            else:
                with open(image_path, "wb") as img_file:
                    img_file.write(image_data)
            
            # Check if caption exists in metadata
            existing_caption = metadata.get('image_path', '')
            
            # Generate caption and description with LLM
            if width >= self.MIN_IMAGE_SIZE_FOR_LLM and height >= self.MIN_IMAGE_SIZE_FOR_LLM:
                caption, description = self._generate_image_caption_with_llm(image_data)
            else:
                caption, description = "Image", ""
            
            # Build inline text
            if existing_caption and description:
                inline_text = f"[IMAGE: {existing_caption}. {description}]"
            elif existing_caption:
                inline_text = f"[IMAGE: {existing_caption}]"
            elif caption and description:
                inline_text = f"[IMAGE: {caption}. {description}]"
            else:
                inline_text = "[IMAGE: image]"
            
            logger.info(f"Processed image {image_id}: {len(caption)} chars caption, {len(description)} chars description")
            return inline_text
            
        except Exception as e:
            logger.warning(f"Error processing image: {str(e)}")
            return None
    
    def _extract_image_from_pdf(self, file_path: str, page_num: int) -> Optional[bytes]:
        """
        Extract image from PDF page using PyMuPDF.
        
        Args:
            file_path: Path to PDF file
            page_num: Page number (1-indexed)
            
        Returns:
            Image data as bytes or None
        """
        if not PYMUPDF_AVAILABLE:
            return None
        
        try:
            pdf_document = fitz.open(file_path)
            page = pdf_document.load_page(page_num - 1)  # Convert to 0-indexed
            
            image_list = page.get_images()
            
            if image_list:
                # Get first image
                xref = image_list[0][0]
                base_image = pdf_document.extract_image(xref)
                return base_image["image"]
            
            pdf_document.close()
            
        except Exception as e:
            logger.debug(f"Image extraction failed: {str(e)}")
        
        return None
    
    def _generate_image_caption_with_llm(self, image_data: bytes) -> Tuple[str, str]:
        """
        Generate image caption and business description using OpenRouter Vision API.
        
        For charts/graphs: Provides detailed business interpretation
        (e.g., "Company X has been evolving during the last year and achieved financial success")
        
        Args:
            image_data: Image data as bytes
            
        Returns:
            Tuple of (caption, description)
        """
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Prompt for detailed analysis including chart/graph interpretation
            prompt = """Analyze this image in detail for a compliance/AML document review.

Please provide:
1. Factual Description: What do you see? (3-5 lines, specific details)
2. Business Summary: Compliance and business relevance
   - If it's a chart/graph: What trends, patterns, or insights does it show?
   - If it's a table: What are the key financial/business metrics?
   - If it's a signature/form: What is its purpose?
   - Why is this important for AML/compliance review?"""

            data = {
                "model": Config.VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                f"{Config.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # Longer timeout for detailed analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Parse the response
                lines = content.split('\n')
                factual_desc = ""
                business_summary = ""
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith("1.") or line.lower().startswith("factual"):
                        current_section = "factual"
                        factual_desc = line.replace("1. Factual Description:", "").replace("Factual Description:", "").strip()
                    elif line.startswith("2.") or line.lower().startswith("business"):
                        current_section = "business"
                        business_summary = line.replace("2. Business Summary:", "").replace("Business Summary:", "").strip()
                    elif current_section == "factual" and line:
                        factual_desc += " " + line
                    elif current_section == "business" and line:
                        business_summary += " " + line
                
                # Generate caption from factual description
                caption = factual_desc.strip()[:100] + "..." if len(factual_desc) > 100 else factual_desc.strip()
                if not caption:
                    caption = "Image"
                
                return caption, business_summary.strip()
            else:
                logger.warning(f"OpenRouter Vision API error: {response.status_code}")
                return "Image", ""
                
        except Exception as e:
            logger.warning(f"Image captioning failed: {str(e)}")
            return "Image", ""


# Backward compatibility alias
LangChainLoader = LangChainRAGLoader