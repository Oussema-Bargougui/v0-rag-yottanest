#!/usr/bin/env python3
"""
Test script for the FastAPI RAG server
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test config import
        from config import Config
        print("✓ Config imported successfully")
        
        # Test data loader import
        from modules.data_loader import MultimodalDataLoader
        print("✓ MultimodalDataLoader imported successfully")
        
        # Test FastAPI import
        from fastapi import FastAPI
        print("✓ FastAPI imported successfully")
        
        # Test main app import
        import main
        print("✓ Main app imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from config import Config
        
        print("\nTesting configuration...")
        print(f"OpenRouter API configured: {bool(Config.OPENROUTER_API_KEY)}")
        print(f"Storage path: {Config.get_storage_path()}")
        print(f"API Host: {Config.API_HOST}")
        print(f"API Port: {Config.API_PORT}")
        
        return True
        
    except Exception as e:
        print(f"✗ Config test failed: {str(e)}")
        return False

def test_data_loader():
    """Test data loader initialization."""
    try:
        from modules.data_loader import MultimodalDataLoader
        
        print("\nTesting data loader...")
        loader = MultimodalDataLoader()
        print(f"✓ Data loader initialized")
        print(f"Storage path: {loader.storage_path}")
        print(f"Images path: {loader.images_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Data loader test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=== RAG Researcher FastAPI Server Test ===\n")
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test configuration
    if not test_config():
        success = False
    
    # Test data loader
    if not test_data_loader():
        success = False
    
    if success:
        print("\n✓ All tests passed! The server should work correctly.")
        print("\nTo start the server, run:")
        print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    main()