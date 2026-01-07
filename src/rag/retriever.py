"""
Nephrology Knowledge Retriever
Semantic search over vector database
"""

import chromadb
from src.embeddings.embedding_manager import get_embedding_model
from src.utils.logger import log_system

VECTOR_DB_PATH = "data/vector_store/chroma_db"
COLLECTION_NAME = "nephrology_reference"


class NephrologyRetriever:
    """Retriever for nephrology knowledge base"""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        
        print(" Loading embedding model...")
        self.model = get_embedding_model()
        
        print(" Connecting to vector store...")
        # FIXED: Using PersistentClient instead of Client with Settings
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        
        # Load collection
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            count = self.collection.count()
            print(f" Loaded collection with {count} chunks")
        except Exception as e:
            print(f" Error loading collection: {e}")
            raise
        
        log_system("Nephrology Retriever initialized")

    def retrieve(self, query: str, top_k: int = None):
        """
        Retrieve relevant chunks for query
        
        Args:
            query: Search query
            top_k: Number of results (overrides default)
        
        Returns:
            List of retrieved chunks with metadata
        """
        k = top_k or self.top_k
        
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Search vector store
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        # Format results
        retrieved = []
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            retrieved.append({
                "rank": i + 1,
                "text": doc,
                "page": meta.get("page"),
                "chunk_id": meta.get("chunk_id"),
                "similarity": 1 - dist
            })
        
        log_system(f"Retrieved {len(retrieved)} chunks for query: {query[:50]}...")
        
        return retrieved
    
    def get_context_string(self, retrieved_chunks):
        """Format retrieved chunks as context string"""
        context_parts = []
        
        for chunk in retrieved_chunks:
            context_parts.append(
                f"[Page {chunk['page']}]\n{chunk['text']}"
            )
        
        return "\n\n---\n\n".join(context_parts)


# Quick test
if __name__ == "__main__":
    retriever = NephrologyRetriever(top_k=3)
    
    test_query = "What is chronic kidney disease?"
    print(f"\n Test Query: {test_query}")
    
    results = retriever.retrieve(test_query)
    
    print(f"\n Retrieved {len(results)} chunks:")
    for r in results:
        print(f"\n{r['rank']}. Page {r['page']} (similarity: {r['similarity']:.3f})")
        print(f"   {r['text'][:100]}...")