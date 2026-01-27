"""
Configuration Management for RAG Researcher Service

This module handles all configuration settings for the RAG system,
including OpenRouter API credentials, storage paths, and API settings.

Author: Yottanest Team
Version: 2.0.0
"""

import os
from pathlib import Path
from typing import Optional

# Load environment variables
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

class Config:
    """Configuration class for RAG system settings."""
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "chatgpt-4o-mini")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "chatgpt-4o-mini")
    DECOMPOSITION_MODEL: str = os.getenv("DECOMPOSITION_MODEL", "openai/gpt-3.5-turbo")
    
    # Storage Configuration
    STORAGE_PATH: Path = Path(os.getenv("STORAGE_PATH", "./storage"))
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Document Processing Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    SUPPORTED_FORMATS: list = ['.pdf', '.docx', '.txt', '.md']
    
    # Image Processing Settings
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    IMAGE_FORMATS: list = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    # Retrieval Configuration
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"
    RETRIEVER_CONFIG: dict = {
        "dense_top_k": 30,
        "sparse_top_k": 20,
        "max_candidates": 40,
        "rerank_top_n": 10,
        "dense_weight": 0.6,
        "sparse_weight": 0.4
    }
    
    # Chunking Configuration
    CHUNK_SIZE_TOKENS: int = 400  # Target chunk size in tokens
    CHUNK_OVERLAP_TOKENS: int = 50  # Overlap between chunks
    PRESERVE_HEADERS: bool = True  # Ensure headers are in every chunk
    
    # Query Expansion Configuration
    ENABLE_QUERY_EXPANSION: bool = True
    QUERY_EXPANSION_TERMS: int = 3  # Number of additional terms to generate
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            True if configuration is valid, raises ValueError otherwise
        """
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required")
        
        if not cls.OPENROUTER_BASE_URL:
            raise ValueError("OPENROUTER_BASE_URL is required")
        
        # Create storage directory if it doesn't exist
        cls.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        
        return True
    
    @classmethod
    def get_storage_path(cls, subpath: str = "") -> Path:
        """
        Get storage path for files.
        
        Args:
            subpath: Optional subpath within storage
            
        Returns:
            Full path to storage location
        """
        if subpath:
            return cls.STORAGE_PATH / subpath
        return cls.STORAGE_PATH

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    exit(1)