"""
Test script to verify RAGTextCleaner storage path
"""
import json
from pathlib import Path
from modules.rag_text_cleaner import RAGTextCleaner
from config import Config

print("=" * 60)
print("Testing RAGTextCleaner Storage Path")
print("=" * 60)

# Check config storage path
config_storage = Config.get_storage_path()
print(f"\nConfig storage path: {config_storage}")
print(f"Config storage exists: {config_storage.exists()}")

# Initialize cleaner and check its path
cleaner = RAGTextCleaner()
print(f"\nCleaner storage path: {cleaner.storage_path}")
print(f"Cleaner cleaned path: {cleaner.cleaned_path}")
print(f"Cleaned path exists: {cleaner.cleaned_path.exists()}")

# Load an extraction file
extraction_file = config_storage / "extraction" / "77cd2a46-ab19-4027-81bf-4106bc36c8a9.json"
print(f"\nExtraction file path: {extraction_file}")
print(f"Extraction file exists: {extraction_file.exists()}")

if extraction_file.exists():
    with open(extraction_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Clean the document
    print("\n" + "=" * 60)
    print("Cleaning document...")
    print("=" * 60)
    cleaned = cleaner.clean_extracted_document(data)
    
    # Save cleaned document
    print("\n" + "=" * 60)
    print("Saving cleaned document...")
    print("=" * 60)
    cleaned_path = cleaner.save_cleaned_document(cleaned)
    print(f"Cleaned file saved to: {cleaned_path}")
    
    # Verify file exists
    cleaned_file = Path(cleaned_path)
    print(f"Cleaned file exists: {cleaned_file.exists()}")
    
    # Check storage/cleaned directory
    storage_cleaned = config_storage / "cleaned"
    print(f"\nStorage cleaned dir: {storage_cleaned}")
    print(f"Storage cleaned dir exists: {storage_cleaned.exists()}")
    if storage_cleaned.exists():
        files = list(storage_cleaned.glob("*.json"))
        print(f"Files in storage/cleaned: {len(files)}")
        for f in files:
            print(f"  - {f.name}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)