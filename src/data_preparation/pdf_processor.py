from pypdf import PdfReader
from pathlib import Path
import json
from src.utils.logger import log_system

PDF_PATH = "data/reference_materials/comprehensive-clinical-nephrology.pdf"
OUTPUT_DIR = "data/reference_materials/processed"
CHUNK_SIZE = 1000  
OVERLAP = 100      


def chunk_text(text, chunk_size=1000, overlap=100):
    """
    Chunk text by CHARACTERS (not words)
    
    Args:
        text: Input text
        chunk_size: Characters per chunk
        overlap: Overlapping characters
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def process_pdf():
    """Process PDF into chunks"""
    print(f" Processing PDF: {PDF_PATH}")
    
    reader = PdfReader(PDF_PATH)
    all_chunks = []
    
    print(f" Total pages: {len(reader.pages)}")
    
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        
        if not text or not text.strip():
            continue
        
        # Clean text
        text = text.strip()
        
        # Chunk by characters (not words!)
        chunks = chunk_text(text, CHUNK_SIZE, OVERLAP)
        
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"chunk_{len(all_chunks):05d}",
                "page": page_num,
                "chunk_index": chunk_idx,
                "text": chunk,
                "char_count": len(chunk)
            })
        
        # Progress
        if page_num % 100 == 0:
            print(f"  Processed {page_num}/{len(reader.pages)} pages...")
    
    # Save
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    output_file = f"{OUTPUT_DIR}/chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Stats
    total_chars = sum(c['char_count'] for c in all_chunks)
    avg_chars = total_chars / len(all_chunks) if all_chunks else 0
    
    log_system(f"PDF processed into {len(all_chunks)} chunks")
    print(f"\n Processing complete!")
    print(f"   Total chunks: {len(all_chunks)}")
    print(f"   Avg chunk size: {avg_chars:.0f} characters")
    print(f"   Output: {output_file}")


if __name__ == "__main__":
    process_pdf()

    