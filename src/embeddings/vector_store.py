"""Vector Store Builder"""

import chromadb
from chromadb.config import Settings
import json
from pathlib import Path

CHUNKS_PATH = "data/reference_materials/processed/chunks.json"
VECTOR_DB_PATH = "data/vector_store/chroma_db"
COLLECTION_NAME = "nephrology_reference"
BATCH_SIZE = 100


def build_vector_store():
    from src.embeddings.embedding_manager import get_embedding_model
    
    print(" Loading embedding model...")
    model = get_embedding_model()
    
    print(" Initializing ChromaDB...")
    Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    
    # Delete old if exists
    try:
        client.delete_collection(COLLECTION_NAME)
        print(" Deleted old collection")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Nephrology knowledge"}
    )
    
    print(f" Loading chunks...")
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)
    
    total = len(chunks)
    print(f" Loaded {total} chunks")
    
    # Process in batches
    print(f"\n Processing {total//BATCH_SIZE + 1} batches...")
    
    for i in range(0, total, BATCH_SIZE):
        end = min(i + BATCH_SIZE, total)
        batch = chunks[i:end]
        
        docs = [c["text"] for c in batch]
        metas = [{"page": c["page"], "chunk_id": c.get("chunk_id", f"chunk_{j}")} 
                 for j, c in enumerate(batch)]
        ids = [f"id_{i+j}" for j in range(len(batch))]
        
        # Embeddings
        embeds = model.encode(docs, show_progress_bar=False).tolist()
        
        # Add
        collection.add(documents=docs, embeddings=embeds, metadatas=metas, ids=ids)
        
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"  Processed {i}/{total}...")
    
    print(f"\n Complete! {total} chunks in {COLLECTION_NAME}")


if __name__ == "__main__":
    build_vector_store()