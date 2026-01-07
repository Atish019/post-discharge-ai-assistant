import os
from groq import Groq
from src.utils.logger import log_system
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class GroqClient:
    """Simple Groq LLM wrapper with error handling"""
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.3):
        """
        Initialize Groq client
        
        Args:
            model_name: Groq model to use
            temperature: Generation temperature (0.0-1.0)
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(" GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        
        log_system(f"GroqClient initialized: {model_name}")
    
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = None, max_tokens: int = 1000) -> str:
        """
        Generate response from Groq
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Override default temperature
            max_tokens: Max response length
        
        Returns:
            Generated text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            log_system(f"Groq API error: {e}")
            raise Exception(f"Failed to generate response: {e}")