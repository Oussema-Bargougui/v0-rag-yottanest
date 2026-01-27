Production-Grade Text Cleaning Layer for Multimodal RAG System (Bank-Level)

1. Purpose of This Component

The RAGTextCleaner is a dedicated, lossless, production-grade text normalization layer for the RAG ingestion pipeline.

Its mission is:

Clean extracted text WITHOUT destroying information,
preserve metadata, structure, and semantic meaning,
and prepare the content for chunking and embedding.

This cleaner operates after extraction and before chunking.

2. Why This Is Needed

The current extraction output:

contains noise (OCR artifacts, broken spacing, control chars)

contains page-level structure (which we MUST keep)

contains images and tables already converted to text

contains critical metadata (doc_id, page_number, etc.)

Naive cleaning breaks RAG accuracy.
This cleaner is designed to never lose data.

3. Strict Rules (NON-NEGOTIABLE)
❌ The cleaner MUST NOT:

remove characters (€, £, %, numbers, symbols)

remove punctuation

remove line breaks

remove table text

remove image descriptions

flatten layout

normalize to ASCII

mask emails, URLs, phone numbers

merge pages

change metadata

✅ The cleaner MUST:

operate per page

preserve metadata 100%

be deterministic

be idempotent

be reversible (no data loss)

run fast (milliseconds per page)

4. Input Format (MANDATORY)

The cleaner receives one extracted JSON file from:

storage/extraction/<doc_id>.json


Example (simplified):

{
  "doc_id": "uuid",
  "filename": "report.pdf",
  "pages": [
    {
      "page_number": 8,
      "text": "...",
      "metadata": {
        "has_images": true,
        "has_tables": false
      }
    }
  ]
}

5. Output Format (MUST BE IDENTICAL STRUCTURE)

The cleaner returns the same JSON schema, only with cleaned text.

{
  "doc_id": "uuid",
  "filename": "report.pdf",
  "pages": [
    {
      "page_number": 8,
      "text": "CLEANED TEXT",
      "metadata": {
        "has_images": true,
        "has_tables": false
      }
    }
  ]
}

6. Architecture
Component name:
rag_text_cleaner.py

Class name:
class RAGTextCleaner:

Public method:
def clean_extracted_document(self, extracted_json: dict) -> dict

7. Cleaning Strategy (LOSSLESS)
7.1 Allowed Cleaning (SAFE)
1. Remove control characters
\u0007 \x0c \x0b \x00

2. Normalize whitespace (without flattening)
"hello     world" → "hello world"

3. Normalize line breaks

Reduce 4+ line breaks → 2

Preserve paragraphs

Preserve bullets

Preserve tables

4. Normalize broken hyphenation
finan-
cial → financial

5. Normalize quotes and dashes (SAFE)
“ ” → "
— – → -

7.2 Forbidden Cleaning

❌ DO NOT remove:

symbols

currencies

numbers

punctuation

URLs

emails

table delimiters

image blocks

metadata

page boundaries

8. Page-Level Cleaning (CRITICAL)

Cleaning MUST be applied page by page.

for page in extracted_json["pages"]:
    page["text"] = clean_page_text(page["text"])


DO NOT concatenate pages.

9. Metadata Preservation (MANDATORY)

The cleaner MUST keep:

{
  "doc_id",
  "filename",
  "page_number",
  "has_images",
  "has_tables",
  "image_ids"
}


Metadata must be copied unchanged.

10. Image Blocks (DO NOT TOUCH)

If text contains:

[IMAGE]
Caption: ...
Description: ...


The cleaner must:

keep it

preserve location

clean only spacing

11. Table Blocks (DO NOT TOUCH STRUCTURE)

If text contains table text:

keep line breaks

keep alignment

clean only extra spaces

do not reformat

12. Storage

Cleaned output must be saved to:

storage/cleaned/<doc_id>.json


Rules:

create folder if not exists

never overwrite original extraction

one cleaned file per document

deterministic naming

13. Testing (MANDATORY)
CLI test (NO FastAPI endpoint yet)

Command:

python rag_text_cleaner.py storage/extraction/<doc_id>.json


Expected:

prints summary

saves cleaned file

logs time

no crash

no data loss

14. Logging

Log:

doc_id

number of pages

characters before/after

time taken

warnings (if any)

15. Performance Requirements

< 50 ms per page

No LLM calls

No IO inside loops

Pure Python

16. Integration (NEXT STAGE, NOT NOW)

Later:

upload → extract → clean → chunk → embed


For now, this is standalone.

17. Summary (IMPORTANT)

This cleaner is:

RAG-safe

lossless

metadata-preserving

page-aware

bank-grade

deterministic

production-ready

18. Final Instruction to GLM (MANDATORY)

DO NOT touch extraction code

DO NOT touch upload endpoint

DO NOT touch chunking

ONLY create this new cleaner( under the rag_researcher/modules folder)

Follow this spec exactly

Ask if anything is unclear