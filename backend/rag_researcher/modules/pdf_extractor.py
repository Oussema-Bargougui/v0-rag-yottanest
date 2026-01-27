import pytesseract
from pdf2image import convert_from_path
import pdfplumber
import os

# OCR function for scanned PDFs (convert pages to images and extract text)
def ocr_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image)
    return text


# Extract text from normal (text-based) PDFs using pdfplumber
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text


# Extract tables from PDFs using pdfplumber
def extract_tables_from_pdf(pdf_path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


# Save extracted text and tables to a text file
def save_to_txt(text, tables, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        # Save text content
        f.write("=" * 50 + "\n")
        f.write("EXTRACTED TEXT\n")
        f.write("=" * 50 + "\n\n")
        f.write(text if text else "No text found")
        f.write("\n\n")

        # Save tables
        f.write("=" * 50 + "\n")
        f.write("EXTRACTED TABLES\n")
        f.write("=" * 50 + "\n\n")
        if tables:
            for i, table in enumerate(tables):
                f.write(f"\nTable {i+1}:\n")
                f.write("-" * 30 + "\n")
                for row in table:
                    clean_row = [str(cell) if cell else "" for cell in row]
                    f.write("\t".join(clean_row) + "\n")
        else:
            f.write("No tables found\n")

    print(f"✓ Extracted data saved to {output_file}")


# Main function to process any PDF (scanned or normal)
def process_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return None
    
    try:
        # 1. Extract text from normal PDF
        print("\n[Step 1/3] Extracting text...")
        text = extract_text_from_pdf(pdf_path)
        
        # 2. If no text is found (scanned PDF), use OCR
        if not text or not text.strip():
            print("  → Scanned PDF detected. Using OCR...")
            text = ocr_pdf(pdf_path)
        else:
            print("  → Text-based PDF detected. Text extracted!")

        # 3. Extract tables from the PDF
        print("\n[Step 2/3] Extracting tables...")
        tables = extract_tables_from_pdf(pdf_path)
        print(f"  → {len(tables)} table(s) detected.")

        return {
            'text': text,
            'tables': tables
        }

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None


# Main runner function
def main(pdf_path):
    print("=" * 50)
    print("PDF DATA EXTRACTOR")
    print("=" * 50)
    print(f"\nProcessing: {pdf_path}")
    
    result = process_pdf(pdf_path)
    
    if result:
        # Save to data.txt in the root folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "data.txt")
        
        print("\n[Step 3/3] Saving results...")
        save_to_txt(result['text'], result['tables'], output_file)
        
        print("\n" + "=" * 50)
        print("✓ EXTRACTION COMPLETE!")
        print("=" * 50)
        print(f"  • Text length: {len(result['text'])} characters")
        print(f"  • Tables found: {len(result['tables'])}")
        print(f"\n✓ Data saved to: {output_file}")
    else:
        print("\n❌ Failed to process the PDF.")


if __name__ == "__main__":
    pdf_path = r"C:\Users\majdz\OneDrive\Pictures\wajdi\Yottanest-mvp\pdf_test.pdf"
    main(pdf_path)