"""
Agent Tools
Tools for database retrieval, web search, and RAG
"""

import sqlite3
import json
from typing import Optional, Dict, List
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import (
    PATIENT_DB_PATH,
    VECTOR_DB_PATH,
    VECTOR_DB_COLLECTION_NAME,
    RAG_TOP_K,
    TAVILY_API_KEY
)

import chromadb
from sentence_transformers import SentenceTransformer

# Web search
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️  Tavily not available. Web search will be limited.")


class PatientDatabaseTool:
    """Tool to retrieve patient data from database"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(PATIENT_DB_PATH)
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"❌ Patient database not found: {self.db_path}")
        
        print(f"✅ Patient Database Tool initialized: {self.db_path}")
    
    def get_patient_by_name(self, patient_name: str) -> Optional[Dict]:
        """
        Retrieve patient discharge report by name
        
        Args:
            patient_name: Patient's full name (case-insensitive)
        
        Returns:
            Patient data dict or None if not found
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Case-insensitive search
            query = """
                SELECT * FROM patients 
                WHERE LOWER(patient_name) = LOWER(?)
            """
            
            cursor.execute(query, (patient_name,))
            result = cursor.fetchone()
            
            conn.close()
            
            if not result:
                return None
            
            # Column names
            columns = [
                'patient_id', 'patient_name', 'date_of_birth', 'gender',
                'admission_date', 'discharge_date', 'primary_diagnosis',
                'secondary_diagnoses', 'medications', 'lab_values',
                'dietary_restrictions', 'follow_up', 'warning_signs',
                'discharge_instructions', 'attending_physician',
                'contact_number', 'emergency_contact'
            ]
            
            # Convert to dict
            patient_data = dict(zip(columns, result))
            
            # Parse JSON fields
            patient_data['secondary_diagnoses'] = json.loads(patient_data['secondary_diagnoses'])
            patient_data['medications'] = json.loads(patient_data['medications'])
            patient_data['lab_values'] = json.loads(patient_data['lab_values'])
            patient_data['emergency_contact'] = json.loads(patient_data['emergency_contact'])
            
            return patient_data
        
        except Exception as e:
            print(f"❌ Error retrieving patient: {e}")
            return None
    
    def search_patients_by_diagnosis(self, diagnosis: str) -> List[Dict]:
        """Search patients by diagnosis"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT patient_name, primary_diagnosis, discharge_date
                FROM patients 
                WHERE LOWER(primary_diagnosis) LIKE LOWER(?)
            """
            
            cursor.execute(query, (f"%{diagnosis}%",))
            results = cursor.fetchall()
            
            conn.close()
            
            patients = []
            for row in results:
                patients.append({
                    "patient_name": row[0],
                    "primary_diagnosis": row[1],
                    "discharge_date": row[2]
                })
            
            return patients
        
        except Exception as e:
            print(f"❌ Error searching patients: {e}")
            return []
    
    def get_all_patient_names(self) -> List[str]:
        """Get list of all patient names"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT patient_name FROM patients ORDER BY patient_name")
            results = cursor.fetchall()
            
            conn.close()
            
            return [row[0] for row in results]
        
        except Exception as e:
            print(f" Error getting patient names: {e}")
            return []


class RAGRetrieverTool:
    """Tool to retrieve relevant context from nephrology knowledge base"""
    
    def __init__(self, vector_db_path: str = None):
        self.vector_db_path = vector_db_path or str(VECTOR_DB_PATH)
        
        if not Path(self.vector_db_path).exists():
            raise FileNotFoundError(f" Vector DB not found: {self.vector_db_path}")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        self.collection = self.client.get_collection(VECTOR_DB_COLLECTION_NAME)
        
        # Initialize embedding model
        print(" Loading embedding model for RAG...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print(f" RAG Retriever Tool initialized")
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = None,
        include_metadata: bool = True
    ) -> Dict:
        """
        Retrieve relevant context from knowledge base
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            include_metadata: Include source metadata
        
        Returns:
            Dict with retrieved documents and metadata
        """
        
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k or RAG_TOP_K
            )
            
            # Format results
            retrieved_docs = []
            
            for i, (doc, metadata) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0]
            )):
                retrieved_docs.append({
                    "rank": i + 1,
                    "content": doc,
                    "page": metadata['page'],
                    "chunk": metadata['chunk'],
                    "source": metadata['source']
                })
            
            # Create context string
            context_text = "\n\n".join([
                f"[Source: Page {doc['page']}]\n{doc['content']}"
                for doc in retrieved_docs
            ])
            
            return {
                "context": context_text,
                "documents": retrieved_docs,
                "query": query,
                "num_results": len(retrieved_docs)
            }
        
        except Exception as e:
            print(f" Error retrieving context: {e}")
            return {
                "context": "",
                "documents": [],
                "query": query,
                "num_results": 0,
                "error": str(e)
            }
    
    def get_citations(self, documents: List[Dict]) -> str:
        """Format citations from retrieved documents"""
        
        citations = []
        for doc in documents:
            citations.append(
                f"- {doc['source']}, Page {doc['page']}, Chunk {doc['chunk']}"
            )
        
        return "\n".join(citations)


class WebSearchTool:
    """Tool for web search using Tavily API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or TAVILY_API_KEY
        
        if not self.api_key:
            print("  TAVILY_API_KEY not found. Web search disabled.")
            self.client = None
        elif not TAVILY_AVAILABLE:
            print("  Tavily package not installed. Web search disabled.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)
            print(" Web Search Tool initialized (Tavily)")
    
    def search(self, query: str, max_results: int = 3) -> Dict:
        """
        Search the web for recent medical information
        
        Args:
            query: Search query
            max_results: Number of results to return
        
        Returns:
            Dict with search results
        """
        
        if not self.client:
            return {
                "results": [],
                "query": query,
                "error": "Web search not available. Check TAVILY_API_KEY."
            }
        
        try:
            # Perform search
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"
            )
            
            # Format results
            formatted_results = []
            
            for result in response.get('results', []):
                formatted_results.append({
                    "title": result.get('title', ''),
                    "url": result.get('url', ''),
                    "content": result.get('content', ''),
                    "score": result.get('score', 0)
                })
            
            return {
                "results": formatted_results,
                "query": query,
                "num_results": len(formatted_results)
            }
        
        except Exception as e:
            print(f" Web search error: {e}")
            return {
                "results": [],
                "query": query,
                "error": str(e)
            }
    
    def format_search_results(self, search_results: Dict) -> str:
        """Format search results for LLM consumption"""
        
        if not search_results.get('results'):
            return "No web search results found."
        
        formatted = f"Web search results for: {search_results['query']}\n\n"
        
        for i, result in enumerate(search_results['results'], 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   Source: {result['url']}\n"
            formatted += f"   {result['content'][:200]}...\n\n"
        
        return formatted


# USAGE EXAMPLES

def test_tools():
    """Test all tools"""
    
    print("="*70)
    print("TESTING AGENT TOOLS")
    print("="*70)
    
    # Test 1: Patient Database Tool
    print("\n Test 1: Patient Database Tool")
    print("-"*70)
    
    db_tool = PatientDatabaseTool()
    
    # Get all patient names
    all_patients = db_tool.get_all_patient_names()
    print(f"Total patients in database: {len(all_patients)}")
    print(f"First 3 patients: {all_patients[:3]}")
    
    # Retrieve specific patient
    if all_patients:
        patient_name = all_patients[0]
        patient_data = db_tool.get_patient_by_name(patient_name)
        
        if patient_data:
            print(f"\n Retrieved patient: {patient_data['patient_name']}")
            print(f"   Diagnosis: {patient_data['primary_diagnosis']}")
            print(f"   Medications: {len(patient_data['medications'])}")
    
    # Test 2: RAG Retriever Tool
    print("\n\n Test 2: RAG Retriever Tool")
    print("-"*70)
    
    rag_tool = RAGRetrieverTool()
    
    test_query = "What are the symptoms of chronic kidney disease?"
    results = rag_tool.retrieve_context(test_query, top_k=3)
    
    print(f"Query: {test_query}")
    print(f"Retrieved {results['num_results']} documents")
    
    if results['documents']:
        print(f"\nTop result (Page {results['documents'][0]['page']}):")
        print(f"{results['documents'][0]['content'][:200]}...")
    
    # Test 3: Web Search Tool
    print("\n\n Test 3: Web Search Tool")
    print("-"*70)
    
    search_tool = WebSearchTool()
    
    if search_tool.client:
        search_results = search_tool.search(
            "latest treatment for chronic kidney disease",
            max_results=2
        )
        
        print(f"Query: {search_results['query']}")
        print(f"Found {search_results['num_results']} results")
        
        if search_results['results']:
            print(f"\nTop result:")
            print(f"  Title: {search_results['results'][0]['title']}")
            print(f"  URL: {search_results['results'][0]['url']}")
    else:
        print("  Web search not available")
    
    print("\n" + "="*70)
    print(" ALL TOOL TESTS COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    try:
        test_tools()
    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()


       