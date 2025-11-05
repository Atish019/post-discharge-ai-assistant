"""
Clinical AI Agent
Medical expert with RAG (nephrology knowledge) and web search
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.llm.groq_client import GroqLLMClient
from src.agents.agent_tools import RAGRetrieverTool, WebSearchTool
from config.settings import MEDICAL_DISCLAIMER


class ClinicalAgent:
    """
    Clinical AI Agent - Medical Expert
    
    Responsibilities:
    - Answer medical questions using nephrology knowledge base (RAG)
    - Provide evidence-based medical information
    - Use web search for latest research when needed
    - Always include citations and sources
    - Emphasize consulting healthcare providers
    """
    
    def __init__(self):
        """Initialize Clinical Agent"""
        
        self.llm = GroqLLMClient()
        self.rag_tool = RAGRetrieverTool()
        self.web_search_tool = WebSearchTool()
        
        # Agent state
        self.conversation_history = []
        self.patient_context = None
        
        # System prompt for clinical behavior
        self.system_prompt = """You are an expert Clinical AI Assistant specializing in nephrology and post-discharge patient care.

Your responsibilities:
1. Answer medical questions using evidence-based information
2. Use the provided medical context from nephrology textbooks
3. Always cite your sources (page numbers, references)
4. Emphasize that patients should consult their healthcare provider
5. Be clear, accurate, and professional

Guidelines:
- ALWAYS base answers on provided medical context
- Include citations in format: [Source: Page X]
- If context doesn't have enough info, acknowledge limitations
- Never diagnose or change treatment plans
- Remind patients to contact their doctor for urgent concerns
- Use clear, patient-friendly language while maintaining medical accuracy

Remember: You provide information and guidance, but final medical decisions must be made by healthcare professionals."""
        
        print("✅ Clinical Agent initialized with RAG and Web Search")
    
    def set_patient_context(self, patient_context: str):
        """Set patient context from Receptionist Agent"""
        self.patient_context = patient_context
    
    def answer_medical_query(
        self,
        query: str,
        use_web_search: bool = False
    ) -> Dict:
        """
        Answer medical query using RAG and optionally web search
        
        Args:
            query: Patient's medical question
            use_web_search: Whether to also search the web
        
        Returns:
            Dict with answer, sources, and citations
        """
        
        # Step 1: Retrieve relevant context from knowledge base
        print(f"\n🔍 Retrieving relevant medical context...")
        rag_results = self.rag_tool.retrieve_context(query, top_k=5)
        
        has_relevant_context = rag_results['num_results'] > 0
        
        # Step 2: Decide if web search is needed
        need_web_search = use_web_search or not has_relevant_context
        
        web_results = None
        if need_web_search and self.web_search_tool.client:
            print(f"🌐 Searching web for additional information...")
            web_results = self.web_search_tool.search(
                query=f"nephrology {query}",
                max_results=3
            )
        
        # Step 3: Generate answer using LLM with context
        answer = self._generate_clinical_answer(
            query=query,
            rag_context=rag_results,
            web_results=web_results
        )
        
        # Step 4: Compile response
        response = {
            "answer": answer,
            "rag_sources": rag_results['documents'],
            "web_sources": web_results['results'] if web_results else [],
            "used_rag": has_relevant_context,
            "used_web": web_results is not None and len(web_results.get('results', [])) > 0,
            "query": query
        }
        
        return response
    
    def _generate_clinical_answer(
        self,
        query: str,
        rag_context: Dict,
        web_results: Optional[Dict]
    ) -> str:
        """Generate clinical answer using LLM"""
        
        # Build prompt with all context
        prompt_parts = []
        
        # Patient context
        if self.patient_context:
            prompt_parts.append(f"PATIENT INFORMATION:\n{self.patient_context}\n")
        
        # RAG context
        if rag_context['num_results'] > 0:
            prompt_parts.append(f"MEDICAL REFERENCE CONTEXT:\n{rag_context['context']}\n")
        
        # Web search results
        if web_results and web_results.get('results'):
            web_context = self.web_search_tool.format_search_results(web_results)
            prompt_parts.append(f"RECENT MEDICAL LITERATURE:\n{web_context}\n")
        
        # The question
        prompt_parts.append(f"PATIENT QUESTION:\n{query}\n")
        
        # Instructions
        prompt_parts.append("""
Please provide a detailed, medically accurate answer:
1. Address the patient's question directly
2. Use information from the provided medical context
3. Include citations [Source: Page X] for medical facts
4. Provide actionable guidance when appropriate
5. Remind patient to consult their healthcare provider

Keep the answer clear, professional, and patient-friendly.""")
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            answer = self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3  # Low for medical accuracy
            )
            
            # Add medical disclaimer
            answer += f"\n\n{MEDICAL_DISCLAIMER}"
            
            return answer
        
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return f"I apologize, but I encountered an error processing your question. Please consult your healthcare provider directly for medical advice.\n\n{MEDICAL_DISCLAIMER}"
    
    def explain_treatment(self, treatment: str) -> Dict:
        """Explain a specific treatment or medication"""
        
        query = f"Explain {treatment} treatment in nephrology"
        return self.answer_medical_query(query)
    
    def check_symptoms(self, symptoms: str) -> Dict:
        """Provide information about specific symptoms"""
        
        query = f"What do these symptoms mean in kidney disease: {symptoms}"
        return self.answer_medical_query(query)
    
    def get_dietary_advice(self, diagnosis: str) -> Dict:
        """Get dietary recommendations for diagnosis"""
        
        query = f"Dietary recommendations for {diagnosis}"
        return self.answer_medical_query(query)
    
    def format_response_with_sources(self, response: Dict) -> str:
        """Format response with citations"""
        
        formatted = response['answer']
        
        # Add sources section
        if response['rag_sources']:
            formatted += "\n\n" + "="*70
            formatted += "\n📚 **SOURCES FROM MEDICAL TEXTBOOK:**\n"
            
            citations = self.rag_tool.get_citations(response['rag_sources'])
            formatted += citations
        
        if response['web_sources']:
            formatted += "\n\n" + "="*70
            formatted += "\n🌐 **ADDITIONAL WEB SOURCES:**\n"
            
            for source in response['web_sources']:
                formatted += f"- {source['title']}\n  {source['url']}\n"
        
        return formatted


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def test_clinical_agent():
    """Test Clinical Agent"""
    
    print("="*70)
    print("TESTING CLINICAL AGENT")
    print("="*70)
    
    agent = ClinicalAgent()
    
    # Set patient context (simulating handoff from Receptionist)
    patient_context = """Patient Context:
- Name: Test Patient
- Primary Diagnosis: Chronic Kidney Disease Stage 3
- Current Medications: Lisinopril 10mg daily, Furosemide 20mg BID
- Lab Values: Creatinine 2.1, eGFR 45
- Discharge Date: 2024-10-15
- Warning Signs: Swelling, shortness of breath, decreased urine output
"""
    
    agent.set_patient_context(patient_context)
    
    # Test 1: Medical query with RAG
    print("\n📝 Test 1: Medical Query (RAG-based)")
    print("-"*70)
    
    query1 = "What is chronic kidney disease and how is it managed?"
    print(f"Query: {query1}\n")
    
    response1 = agent.answer_medical_query(query1)
    
    print(f"Used RAG: {response1['used_rag']}")
    print(f"Used Web: {response1['used_web']}")
    print(f"\nAnswer:\n{response1['answer'][:500]}...")
    print(f"\nSources: {len(response1['rag_sources'])} medical references")
    
    # Test 2: Symptom check
    print("\n\n📝 Test 2: Symptom Check")
    print("-"*70)
    
    query2 = "I'm experiencing leg swelling. Is this related to my kidney condition?"
    print(f"Query: {query2}\n")
    
    response2 = agent.check_symptoms("leg swelling")
    
    formatted = agent.format_response_with_sources(response2)
    print(f"Answer:\n{formatted[:600]}...\n")
    
    # Test 3: Treatment explanation
    print("\n\n📝 Test 3: Treatment Explanation")
    print("-"*70)
    
    response3 = agent.explain_treatment("Lisinopril for kidney disease")
    
    print(f"Query: Explain Lisinopril treatment")
    print(f"\nAnswer:\n{response3['answer'][:400]}...")
    
    # Test 4: Web search integration
    print("\n\n📝 Test 4: Web Search Integration")
    print("-"*70)
    
    query4 = "What are the latest SGLT2 inhibitors for kidney protection?"
    print(f"Query: {query4}\n")
    
    response4 = agent.answer_medical_query(query4, use_web_search=True)
    
    print(f"Used RAG: {response4['used_rag']}")
    print(f"Used Web: {response4['used_web']}")
    print(f"Web sources found: {len(response4['web_sources'])}")
    
    print("\n" + "="*70)
    print("✅ CLINICAL AGENT TESTS COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    try:
        test_clinical_agent()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()



        