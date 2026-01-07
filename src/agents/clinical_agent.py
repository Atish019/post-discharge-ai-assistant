from src.rag.retriever import NephrologyRetriever
from src.rag.citation_generator import build_context_with_citations, format_answer_with_citations
from src.llm.groq_client import GroqClient
from src.utils.web_search import TavilyWebSearch
from config.prompts import CLINICAL_SYSTEM_PROMPT
from src.utils.logger import log_system


class ClinicalAIAgent:
    """Clinical AI Agent with RAG + Web Search fallback"""
    
    def __init__(self, top_k: int = 5):
        """
        Initialize Clinical Agent
        
        Args:
            top_k: Number of chunks to retrieve for RAG
        """
        print(" Initializing Clinical AI Agent...")
        
        self.retriever = NephrologyRetriever(top_k=top_k)
        self.llm = GroqClient(
            model_name="llama-3.3-70b-versatile",
            temperature=0.3
        )
        self.web_search = TavilyWebSearch(max_results=3)
        
        log_system("Clinical AI Agent initialized with web search")
        print(" Clinical AI Agent ready (RAG + Web Search)\n")
    
    def answer_medical_query(self, user_query: str) -> dict:
        """
        Answer medical query using RAG-first, web search fallback
        
        Args:
            user_query: Patient's medical question
        
        Returns:
            dict with answer, sources, method used, and metadata
        """
        print(f" Processing query: {user_query[:50]}...")
        
        # Step 1: Try RAG first
        retrieved_chunks = self.retriever.retrieve(user_query)
        
        # Step 2: Decide if web search needed
        needs_web = self._needs_web_search(user_query, retrieved_chunks)
        
        if needs_web:
            print(" Using web search (recent information needed)")
            return self._web_search_answer(user_query)
        
        # Step 3: RAG-based answer
        if not retrieved_chunks:
            return self._no_context_response()
        
        print(f" Using RAG ({len(retrieved_chunks)} chunks)")
        return self._rag_answer(user_query, retrieved_chunks)
    
    def _needs_web_search(self, query: str, chunks: list) -> bool:
        """
        Determine if web search needed
        
        Triggers:
        - Query contains keywords like "latest", "recent", "new"
        - No relevant chunks found in RAG
        """
        web_keywords = [
            "latest", "recent", "new", "current", 
            "2024", "2025", "update", "research",
            "trial", "guidelines", "breakthrough"
        ]
        
        query_lower = query.lower()
        
        # Check keywords
        if any(keyword in query_lower for keyword in web_keywords):
            return True
        
        # Check if RAG failed
        if not chunks or len(chunks) == 0:
            return True
        
        return False
    
    def _rag_answer(self, query: str, chunks: list) -> dict:
        """Generate answer using RAG"""
        
        # Build context with citations
        context, citation_text = build_context_with_citations(chunks)
        
        # Create prompt
        user_prompt = f"""**Medical Question:**
{query}

**Medical Context from Reference:**
{context}

**Instructions:**
Answer using ONLY the information in the context above.
Include page references in your answer.
"""
        
        # Generate with LLM
        print(" Generating answer...")
        try:
            answer = self.llm.generate(
                system_prompt=CLINICAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1500
            )
        except Exception as e:
            log_system(f"LLM generation failed: {e}")
            return {
                "answer": self._error_response(),
                "method": "error",
                "sources": citation_text,
                "chunks_retrieved": len(chunks)
            }
        
        # Format with citations
        final_answer = format_answer_with_citations(answer, citation_text)
        
        log_system(f"RAG response generated ({len(chunks)} sources)")
        
        return {
            "answer": final_answer,
            "method": "rag",
            "sources": citation_text,
            "chunks_retrieved": len(chunks),
            "pages": [c["page"] for c in chunks]
        }
    
    def _web_search_answer(self, query: str) -> dict:
        """Generate answer using web search"""
        
        try:
            # Perform web search
            web_result = self.web_search.search(query)
            
            if web_result.get("error"):
                return self._error_response()
            
            web_answer = web_result.get("answer", "")
            sources = web_result.get("results", [])
            
            if not web_answer and not sources:
                return self._no_web_results()
            
            # Format sources
            sources_text = self._format_web_sources(sources[:3])
            
            # Build final answer
            final_answer = f"""🌐 **Based on Recent Web Search Results**

{web_answer}

---
 **Web Sources:**
{sources_text}

---
⚠️ **Important Notice:**
This information is based on web search results and represents recent findings. 
It is for educational purposes only and does not replace professional medical advice.

Always consult your healthcare provider for medical decisions, especially regarding 
new treatments or research findings.
"""
            
            log_system(f"Web search response generated ({len(sources)} sources)")
            
            return {
                "answer": final_answer,
                "method": "web_search",
                "sources": sources_text,
                "web_sources": sources,
                "chunks_retrieved": 0
            }
        
        except Exception as e:
            log_system(f"Web search failed: {e}")
            return {
                "answer": self._error_response(),
                "method": "error",
                "error": str(e)
            }
    
    def _format_web_sources(self, sources: list) -> str:
        """Format web sources list"""
        if not sources:
            return "No sources available"
        
        formatted = []
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            formatted.append(f"{i}. {title}\n   {url}")
        
        return "\n\n".join(formatted)
    
    def _no_context_response(self) -> dict:
        """Response when no RAG context found"""
        return {
            "answer": """I apologize, but I couldn't find relevant information in the medical reference materials.

⚠️ This may require:
1. Rephrasing your question
2. Asking about a different aspect of nephrology
3. Consulting directly with your healthcare provider

This information is for educational purposes only and does not replace professional medical advice.
""",
            "method": "no_context",
            "sources": "",
            "chunks_retrieved": 0
        }
    
    def _no_web_results(self) -> dict:
        """Response when web search returns nothing"""
        return {
            "answer": """I apologize, but I couldn't find recent information on this topic through web search.

⚠️ For the latest medical information, please consult:
1. Your healthcare provider
2. Medical databases like PubMed
3. Professional medical organizations

This information is for educational purposes only.
""",
            "method": "no_web_results",
            "sources": "",
            "chunks_retrieved": 0
        }
    
    def _error_response(self) -> str:
        """Response when system error occurs"""
        return """I apologize, but I encountered an error while processing your request.

⚠️ For medical questions, please consult your healthcare provider directly.

This information is for educational purposes only and does not replace professional medical advice.
"""


