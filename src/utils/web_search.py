import os
from tavily import TavilyClient
from dotenv import load_dotenv
from src.utils.logger import log_system

load_dotenv()


class TavilyWebSearch:
    """Tavily web search wrapper for recent medical information"""
    
    def __init__(self, max_results: int = 3):
        """
        Initialize Tavily client
        
        Args:
            max_results: Default number of search results
        """
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(" TAVILY_API_KEY not found in .env file")
        
        self.client = TavilyClient(api_key=api_key)
        self.max_results = max_results
        
        log_system("Tavily Web Search initialized")
        print(" Tavily Web Search ready")
    
    def search(self, query: str, max_results: int = None) -> dict:
        """
        Perform web search
        
        Args:
            query: Search query
            max_results: Override default max results
        
        Returns:
            dict with answer and sources
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results or self.max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            log_system(f"Tavily search: {query[:50]}...")
            
            return {
                "answer": response.get("answer", ""),
                "results": response.get("results", []),
                "query": query
            }
        
        except Exception as e:
            log_system(f"Tavily search error: {e}")
            return {
                "answer": "",
                "results": [],
                "query": query,
                "error": str(e)
            }