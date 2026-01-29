# Multi-Document Upload Implementation Guide

## 🎯 Objective
Update `POST /api/v1/collections/{collection_id}/ingest` to accept multiple files at once.

## ✅ Requirements
1. **Accept multiple files** - Change parameter from `file` to `files: List[UploadFile]`
2. **Process each file** - Loop through files and call existing ingestion logic
3. **Clear logging** - Show progress for each file with clean, readable logs
4. **Aggregated result** - Return total chunks processed, not per-file details
5. **NO logic changes** - Keep extraction, chunking, embedding, storage exactly the same
6. **Document tracking** - Already works! Each chunk has `file_name` and `document_id` in metadata

---

## 📁 File to Modify

**File:** `src/api/routes/collections.py`

**Endpoint to update:** `@router.post("/{collection_id}/ingest")`

---

## 🔧 Implementation Steps

### Step 1: Update Imports

Add `List` to the imports:

```python
from typing import Optional, Dict, Any, List  # ← Add List here
```

### Step 2: Update Endpoint Signature

Find the `ingest_into_collection` function and change the parameter:

```python
# OLD CODE
@router.post("/{collection_id}/ingest", response_model=IngestResponse)
async def ingest_into_collection(
    collection_id: str = Path(..., description="The collection ID", min_length=1, max_length=100),
    file: UploadFile = File(..., description="Document file to ingest")  # ← CHANGE THIS
) -> IngestResponse:

# NEW CODE
@router.post("/{collection_id}/ingest", response_model=IngestResponse)
async def ingest_into_collection(
    collection_id: str = Path(..., description="The collection ID", min_length=1, max_length=100),
    files: List[UploadFile] = File(..., description="Document files to ingest (multiple)")  # ← CHANGED
) -> IngestResponse:
```

### Step 3: Update Function Implementation

Replace the entire function body with this:

```python
@router.post(
    "/{collection_id}/ingest",
    response_model=IngestResponse,
    summary="Ingest documents into a collection",
    description="""
    Ingest one or more documents into the specified tenant's collection.

    Multiple files can be uploaded at once. Each file is processed
    independently using the existing ingestion pipeline.

    Document Tracking:
    - Each chunk includes file_name and document_id in metadata
    - Queries can identify which document each chunk came from
    """
)
async def ingest_into_collection(
    collection_id: str = Path(..., description="The collection ID", min_length=1, max_length=100),
    files: List[UploadFile] = File(..., description="Document files to ingest (multiple)")
) -> IngestResponse:
    """
    Ingest multiple documents into a specific tenant collection.

    Args:
        collection_id: The tenant's collection ID
        files: List of document files to ingest

    Returns:
        IngestResponse with aggregated results

    Example:
        POST /api/v1/collections/client123/ingest
        (multipart/form-data with multiple files)
    """
    # Validate files
    if not files or len(files) == 0:
        return IngestResponse(
            success=False,
            message="No files provided",
            error="At least one file is required"
        )

    print(f"\n{'='*80}")
    print(f"[Collections] BATCH INGESTION: {collection_id}")
    print(f"[Collections] Files to process: {len(files)}")
    print(f"{'='*80}")

    # Get the ingestion service for this collection
    try:
        service = _get_ingestion_service_for_collection(collection_id)
    except Exception as e:
        return IngestResponse(
            success=False,
            message="Ingestion service unavailable",
            document_name=f"{len(files)} files",
            error=f"Could not initialize ingestion service: {str(e)}"
        )

    # Process each file
    total_chunks = 0
    successful_files = 0
    failed_files = 0
    first_file_name = files[0].filename if files else ""

    for idx, file in enumerate(files, 1):
        print(f"\n[Collections] Processing file {idx}/{len(files)}: {file.filename}")

        # Validate file
        if not file.filename:
            print(f"[Collections]   ✗ Skipped: No filename")
            failed_files += 1
            continue

        # Check if file type is supported
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in service.get_supported_extensions():
            print(f"[Collections]   ✗ Skipped: Unsupported file type '{ext}'")
            failed_files += 1
            continue

        # Save file temporarily
        temp_dir = None
        temp_path = None

        try:
            temp_dir = tempfile.mkdtemp(prefix="rag_ingest_")
            temp_path = os.path.join(temp_dir, file.filename)

            # Read and save file
            with open(temp_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)

            print(f"[Collections]   ✓ Loaded {os.path.getsize(temp_path)} bytes")

            # Ingest the file
            result = service.ingest_file(temp_path)

            if result.success:
                total_chunks += result.chunk_count
                successful_files += 1
                print(f"[Collections]   ✓ Created {result.chunk_count} chunks")
                print(f"[Collections]   ✓ Stored in rag_{collection_id}")
            else:
                failed_files += 1
                print(f"[Collections]   ✗ Failed: {result.error}")

        except Exception as e:
            failed_files += 1
            print(f"[Collections]   ✗ Error: {str(e)}")

        finally:
            # Cleanup temp file
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"[Collections]   Warning: Could not clean up temp dir: {e}")

    # Print summary
    print(f"\n{'='*80}")
    print(f"[Collections] BATCH INGESTION COMPLETE")
    print(f"[Collections] Total files: {len(files)}")
    print(f"[Collections] Successful: {successful_files}")
    print(f"[Collections] Failed: {failed_files}")
    print(f"[Collections] Total chunks stored: {total_chunks}")
    print(f"{'='*80}\n")

    # Return aggregated result
    if successful_files > 0:
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {successful_files} document(s)",
            document_name=f"{successful_files} file(s) processed",
            document_id="multiple",
            chunk_count=total_chunks,
            metadata={
                "files_processed": successful_files,
                "total_chunks": total_chunks,
                "collection_id": collection_id,
                "failed_files": failed_files
            }
        )
    else:
        return IngestResponse(
            success=False,
            message="Failed to ingest any documents",
            document_name=f"{len(files)} files",
            error="All files failed to process"
        )
```

---

## 📊 Expected Log Output

When uploading 3 files:

```
================================================================================
[Collections] BATCH INGESTION: my_collection
[Collections] Files to process: 3
================================================================================

[Collections] Processing file 1/3: paper1.pdf
[Collections]   ✓ Loaded 25000 bytes
[Collections]   ✓ Created 150 chunks
[Collections]   ✓ Stored in rag_my_collection

[Collections] Processing file 2/3: paper2.pdf
[Collections]   ✓ Loaded 30000 bytes
[Collections]   ✓ Created 200 chunks
[Collections]   ✓ Stored in rag_my_collection

[Collections] Processing file 3/3: notes.txt
[Collections]   ✓ Loaded 5000 bytes
[Collections]   ✓ Created 50 chunks
[Collections]   ✓ Stored in rag_my_collection

================================================================================
[Collections] BATCH INGESTION COMPLETE
[Collections] Total files: 3
[Collections] Successful: 3
[Collections] Failed: 0
[Collections] Total chunks stored: 400
================================================================================
```

---

## 📤 Expected Response

```json
{
  "success": true,
  "message": "Successfully ingested 3 document(s)",
  "document_name": "3 file(s) processed",
  "document_id": "multiple",
  "chunk_count": 400,
  "metadata": {
    "files_processed": 3,
    "total_chunks": 400,
    "collection_id": "my_collection",
    "failed_files": 0
  }
}
```

---

## 🧪 Testing via Swagger UI

1. Start the service:
   ```bash
   python main.py
   ```

2. Open Swagger UI:
   ```
   http://localhost:8001/docs
   ```

3. Find the endpoint:
   ```
   POST /api/v1/collections/{collection_id}/ingest
   ```

4. Click "Try it out"

5. Fill in:
   - `collection_id`: `my_documents`

6. In the "files" parameter:
   - Click "Choose File"
   - Select multiple files (paper1.pdf, paper2.pdf, notes.txt)
   - You can select multiple files in the file dialog

7. Click "Execute"

8. View the response and logs

---

## ✅ Verification Checklist

- [ ] Endpoint accepts multiple files
- [ ] Each file is processed independently
- [ ] Logs are clear and show progress (file X/Y)
- [ ] Response shows total chunks aggregated
- [ ] If one file fails, others continue
- [ ] Document tracking works (file_name and document_id in metadata)
- [ ] Extraction logic unchanged
- [ ] Chunking logic unchanged
- [ ] Embedding logic unchanged
- [ ] Storage logic unchanged
- [ ] All chunks stored in same collection
- [ ] Query endpoint can find chunks from all documents

---

## 🎯 Document Tracking Verification

After uploading multiple documents, verify tracking by querying:

```bash
curl -X POST http://localhost:8001/api/v1/collections/my_documents/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

The response should include sources from multiple documents, showing that each chunk knows its source document.

---

## 📝 Important Notes

1. **Do NOT change** `IngestionService` - it already handles everything correctly
2. **Do NOT change** chunking, embedding, or storage logic
3. **Only change** the API endpoint to loop through files
4. **Document tracking** is automatic - each chunk has metadata:
   - `file_name`: Original filename
   - `document_id`: Unique ID for the document
   - `chunk_id`: Unique ID for the chunk
5. **Query endpoint** will automatically find chunks from all uploaded documents
6. **Error handling** - if one file fails, continue with others
7. **No detailed summary** - just aggregated counts

---

## 🚨 If Something Goes Wrong

1. Check logs - they should show which file failed and why
2. Verify file types are supported (PDF, TXT, HTML, DOCX)
3. Check Qdrant connection
4. Ensure collection exists or is created automatically

---

## 🎉 Success Indicators

✅ Can upload 5+ files at once  
✅ All chunks stored in same collection  
✅ Logs show clear progress for each file  
✅ Response shows total chunks across all files  
✅ Query returns answers from multiple documents  
✅ Each source in response shows correct file name