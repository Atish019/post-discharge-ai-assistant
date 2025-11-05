"""
PDF Processor for Nephrology Reference Book
Processes 1547-page PDF into chunks with embeddings
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import pypdf

# Text processing
#from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sentence_transformers import SentenceTransformer

# Vector store
import chromadb
from chromadb.config import Settings


class NephrologyPDFProcessor:
    """Process nephrology PDF for RAG"""
    
    def __init__(
        self,
        pdf_path: str,
        output_dir: str = "data/reference_materials/processed",
        vector_db_path: str = "data/vector_store/chroma_db"
    ):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.vector_db_path = Path(vector_db_path)
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model (free HuggingFace)
        print(" Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print(" Embedding model loaded!\n")
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # ~800-1000 tokens
            chunk_overlap=100,  # Overlap for context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def extract_text_from_pdf(self) -> List[Dict]:
        """Extract text from PDF page by page"""
        print(f" Reading PDF: {self.pdf_path}")
        print(" This may take 5-10 minutes for 1547 pages...\n")
        
        pages_data = []
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                print(f" Total Pages: {total_pages}\n")
                
                for page_num in tqdm(range(total_pages), desc="Extracting pages"):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        # Clean text
                        text = self._clean_text(text)
                        
                        if text.strip():  # Only save non-empty pages
                            pages_data.append({
                                "page_number": page_num + 1,
                                "text": text,
                                "char_count": len(text)
                            })
                    
                    except Exception as e:
                        print(f"\n  Error on page {page_num + 1}: {e}")
                        continue
        
        except Exception as e:
            print(f" Error reading PDF: {e}")
            raise
        
        print(f"\n Extracted {len(pages_data)} pages successfully!")
        return pages_data
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep medical terms
        text = re.sub(r'[^\w\s\.\,\-\(\)\%\/\:]', '', text)
        return text.strip()
    
    def create_chunks(self, pages_data: List[Dict]) -> List[Dict]:
        """Split pages into chunks with metadata"""
        print("\n Creating chunks...")
        
        all_chunks = []
        chunk_id = 0
        
        for page_data in tqdm(pages_data, desc="Chunking pages"):
            page_num = page_data["page_number"]
            text = page_data["text"]
            
            # Split page text into chunks
            chunks = self.text_splitter.split_text(text)
            
            for i, chunk_text in enumerate(chunks):
                all_chunks.append({
                    "chunk_id": f"chunk_{chunk_id:06d}",
                    "page_number": page_num,
                    "chunk_index": i,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "metadata": {
                        "source": "comprehensive-clinical-nephrology",
                        "page": page_num,
                        "chunk": i
                    }
                })
                chunk_id += 1
        
        print(f" Created {len(all_chunks)} chunks from {len(pages_data)} pages")
        return all_chunks
    
    def save_chunks_to_json(self, chunks: List[Dict]):
        """Save chunks to JSON file"""
        output_file = self.output_dir / "chunks.json"
        
        print(f"\n Saving chunks to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        print(f" Saved {len(chunks)} chunks to JSON")
    
    def create_embeddings_and_store(self, chunks: List[Dict]):
        """Create embeddings and store in ChromaDB"""
        print("\n Creating embeddings and storing in ChromaDB...")
        print(" This will take 10-15 minutes...\n")
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path=str(self.vector_db_path))
        
        # Create or get collection
        try:
            client.delete_collection("nephrology_knowledge")
        except:
            pass
        
        collection = client.create_collection(
            name="nephrology_knowledge",
            metadata={"description": "Comprehensive Clinical Nephrology textbook"}
        )
        
        # Process in batches (ChromaDB has limits)
        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        for batch_num in tqdm(range(total_batches), desc="Processing batches"):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(chunks))
            batch_chunks = chunks[start_idx:end_idx]
            
            # Prepare data for ChromaDB
            ids = [chunk["chunk_id"] for chunk in batch_chunks]
            texts = [chunk["text"] for chunk in batch_chunks]
            metadatas = [chunk["metadata"] for chunk in batch_chunks]
            
            # Create embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Add to ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
        
        print(f"\n Stored {len(chunks)} chunks in ChromaDB!")
        print(f" Vector DB location: {self.vector_db_path}")
    
    def process_full_pipeline(self):
        """Run complete processing pipeline"""
        print("="*70)
        print("NEPHROLOGY PDF PROCESSING PIPELINE")
        print("="*70)
        print(f" PDF: {self.pdf_path}")
        print(f" Output: {self.output_dir}")
        print(f"  Vector DB: {self.vector_db_path}")
        print("="*70 + "\n")
        
        # Step 1: Extract text from PDF
        pages_data = self.extract_text_from_pdf()
        
        # Step 2: Create chunks
        chunks = self.create_chunks(pages_data)
        
        # Step 3: Save chunks to JSON
        self.save_chunks_to_json(chunks)
        
        # Step 4: Create embeddings and store in ChromaDB
        self.create_embeddings_and_store(chunks)
        
        # Summary
        print("\n" + "="*70)
        print(" PROCESSING COMPLETE!")
        print("="*70)
        print(f" Statistics:")
        print(f"   - Total Pages: {len(pages_data)}")
        print(f"   - Total Chunks: {len(chunks)}")
        print(f"   - Avg Chunk Size: {sum(c['char_count'] for c in chunks) / len(chunks):.0f} chars")
        print(f"\n Files Created:")
        print(f"   - {self.output_dir}/chunks.json")
        print(f"   - {self.vector_db_path}/chroma.sqlite3")
        print("\n Next Step: Test RAG retrieval!")
        print("="*70)
    
    def test_retrieval(self, query: str, top_k: int = 5):
        """Test semantic search"""
        print(f"\n Testing retrieval with query: '{query}'")
        
        # Load ChromaDB
        client = chromadb.PersistentClient(path=str(self.vector_db_path))
        collection = client.get_collection("nephrology_knowledge")
        
        # Create query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        print(f"\n Top {top_k} Results:")
        print("-" * 70)
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"\n{i+1}. Page {metadata['page']}, Chunk {metadata['chunk']}")
            print(f"   {doc[:200]}...")
        
        return results


def main():
    """Main execution"""
    
    # PDF path
    pdf_path = r"C:\Users\atish\Desktop\post-discharge-ai-assistant\data\reference_materials\comprehensive-clinical-nephrology.pdf"
    
    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f" PDF not found: {pdf_path}")
        print("Please check the file path!")
        return
    
    # Initialize processor
    processor = NephrologyPDFProcessor(pdf_path)
    
    # Check if already processed
    chunks_file = processor.output_dir / "chunks.json"
    vector_db_file = processor.vector_db_path / "chroma.sqlite3"
    
    if chunks_file.exists() and vector_db_file.exists():
        print("  WARNING: Processed files already exist!")
        print(f"   - {chunks_file}")
        print(f"   - {vector_db_file}")
        
        response = input("\n Re-process PDF? This will take 20-30 minutes. (yes/no): ")
        
        if response.lower() != 'yes':
            print("\n Using existing processed data.")
            print("\n Running test query...")
            processor.test_retrieval("What is chronic kidney disease?")
            return
    
    # Process PDF
    processor.process_full_pipeline()
    
    # Test retrieval
    print("\n" + "="*70)
    print(" TESTING RAG RETRIEVAL")
    print("="*70)
    processor.test_retrieval("What is chronic kidney disease?", top_k=3)
    processor.test_retrieval("Treatment for diabetic nephropathy", top_k=3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Processing cancelled by user")
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()


