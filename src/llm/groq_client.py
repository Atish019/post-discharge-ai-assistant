"""
Groq LLM Client
Wrapper for Groq API with error handling and retry logic
"""

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, List, Dict
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS,
    GROQ_TOP_P
)


class GroqLLMClient:
    """Groq LLM client with retry logic and error handling"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """Initialize Groq client"""
        
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError(" GROQ_API_KEY not found! Set it in .env file")
        
        self.client = Groq(api_key=self.api_key)
        
        # Configuration
        self.model_name = model_name or GROQ_MODEL_NAME
        self.temperature = temperature or GROQ_TEMPERATURE
        self.max_tokens = max_tokens or GROQ_MAX_TOKENS
        self.top_p = GROQ_TOP_P
        
        print(f" Groq Client initialized with model: {self.model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Send chat completion request to Groq
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Enable streaming (for future use)
        
        Returns:
            Response content as string
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                top_p=self.top_p,
                stream=stream
            )
            
            if stream:
                # For streaming responses (future implementation)
                return response
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f" Groq API Error: {e}")
            raise
    
    def simple_query(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Simple query interface
        
        Args:
            prompt: User query
            system_message: Optional system prompt
            temperature: Override default temperature
        
        Returns:
            Response string
        """
        
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat_completion(
            messages=messages,
            temperature=temperature
        )
    
    def chat_with_context(
        self,
        user_message: str,
        context: str,
        system_message: Optional[str] = None
    ) -> str:
        """
        Query with context (for RAG)
        
        Args:
            user_message: User's question
            context: Retrieved context from RAG
            system_message: System instructions
        
        Returns:
            Response string
        """
        
        # Build prompt with context
        prompt = f"""Context from medical reference:
{context}

Based on the above context, please answer the following question:
{user_message}

Provide a detailed, medically accurate response with citations."""
        
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat_completion(messages=messages)
    
    def get_model_info(self) -> Dict:
        """Get current model configuration"""
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }



# USAGE EXAMPLES

def test_groq_client():
    """Test Groq client functionality"""
    
    print("="*70)
    print("TESTING GROQ CLIENT")
    print("="*70)
    
    # Initialize client
    client = GroqLLMClient()
    
    # Test 1: Simple query
    print("\n Test 1: Simple Query")
    print("-"*70)
    response = client.simple_query(
        prompt="What is chronic kidney disease? Explain in 2 sentences.",
        system_message="You are a medical expert. Provide concise, accurate information."
    )
    print(f"Response: {response}\n")
    
    # Test 2: Chat with context (simulating RAG)
    print("\n Test 2: RAG-style Query with Context")
    print("-"*70)
    
    sample_context = """
    Chronic kidney disease (CKD) is defined as abnormalities of kidney structure 
    or function, present for more than 3 months. CKD is classified into 5 stages 
    based on GFR levels. Stage 3 CKD has GFR between 30-59 ml/min/1.73m².
    """
    
    response = client.chat_with_context(
        user_message="What is Stage 3 CKD?",
        context=sample_context,
        system_message="You are a nephrology expert. Answer based on the provided context."
    )
    print(f"Response: {response}\n")
    
    # Test 3: Model info
    print("\n Test 3: Model Configuration")
    print("-"*70)
    info = client.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print(" ALL TESTS PASSED!")
    print("="*70)


if __name__ == "__main__":
    try:
        test_groq_client()
    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()

