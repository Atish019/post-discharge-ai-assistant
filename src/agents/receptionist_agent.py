"""
Receptionist Agent
Handles patient greeting, data retrieval, and routing to Clinical Agent
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Literal

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.llm.groq_client import GroqLLMClient
from src.agents.agent_tools import PatientDatabaseTool
from config.settings import MEDICAL_DISCLAIMER


class ReceptionistAgent:
    """
    Receptionist Agent - First point of contact
    
    Responsibilities:
    - Greet patients warmly
    - Ask for patient name
    - Retrieve patient discharge report from database
    - Ask follow-up questions based on discharge info
    - Identify medical queries and route to Clinical Agent
    - Handle general inquiries
    """
    
    def __init__(self):
        """Initialize Receptionist Agent"""
        
        self.llm = GroqLLMClient()
        self.db_tool = PatientDatabaseTool()
        
        # Agent state
        self.patient_name = None
        self.patient_data = None
        self.conversation_history = []
        
        # System prompt for receptionist behavior
        self.system_prompt = """You are a friendly and professional medical receptionist AI assistant for post-discharge patient care.

Your responsibilities:
1. Greet patients warmly and ask for their name
2. Once you have their name, retrieve their discharge information
3. Ask follow-up questions about their recovery based on their discharge report
4. Identify when patients have medical questions that need clinical expertise
5. Be empathetic and supportive

Guidelines:
- Always be warm, friendly, and professional
- Keep questions clear and simple
- If patient mentions symptoms or medical concerns, acknowledge and route to clinical team
- Never provide medical advice - that's for the Clinical AI Agent
- Focus on patient comfort and understanding their needs

Remember: You're the first point of contact, making patients feel heard and cared for."""
        
        print("✅ Receptionist Agent initialized")
    
    def greet_patient(self) -> str:
        """Initial greeting to patient"""
        
        greeting = f"""Hello! Welcome to the Post-Discharge Care Assistant. 🏥

{MEDICAL_DISCLAIMER}

I'm here to help you with any questions about your recovery and discharge instructions.

**To get started, could you please tell me your full name?**

(Example: John Smith)"""
        
        return greeting
    
    def process_patient_name(self, name: str) -> Dict:
        """
        Process patient name and retrieve data
        
        Args:
            name: Patient's full name
        
        Returns:
            Dict with status and response
        """
        
        # Clean name
        name = name.strip()
        
        if not name or len(name) < 3:
            return {
                "status": "invalid_name",
                "response": "I didn't quite catch that. Could you please provide your full name? (First and Last name)"
            }
        
        # Retrieve patient data
        patient_data = self.db_tool.get_patient_by_name(name)
        
        if not patient_data:
            # Try to find similar names
            all_names = self.db_tool.get_all_patient_names()
            
            # Simple fuzzy matching
            similar_names = [n for n in all_names if name.lower() in n.lower() or n.lower() in name.lower()]
            
            if similar_names:
                suggestion = f"\n\nDid you mean one of these?\n" + "\n".join([f"- {n}" for n in similar_names[:3]])
            else:
                suggestion = "\n\nPlease check your name spelling and try again."
            
            return {
                "status": "not_found",
                "response": f"I couldn't find a discharge report for '{name}' in our system.{suggestion}"
            }
        
        # Store patient data
        self.patient_name = name
        self.patient_data = patient_data
        
        # Generate personalized response
        response = self._generate_patient_greeting()
        
        return {
            "status": "success",
            "response": response,
            "patient_data": patient_data
        }
    
    def _generate_patient_greeting(self) -> str:
        """Generate personalized greeting after finding patient"""
        
        if not self.patient_data:
            return "Error: Patient data not loaded"
        
        # Extract key info
        diagnosis = self.patient_data['primary_diagnosis']
        discharge_date = self.patient_data['discharge_date']
        medications = self.patient_data['medications']
        
        # Use LLM to generate warm, personalized greeting
        prompt = f"""Patient found in system:
- Name: {self.patient_name}
- Diagnosis: {diagnosis}
- Discharge Date: {discharge_date}
- Medications: {len(medications)} prescribed

Generate a warm, personalized greeting for this patient. Include:
1. Welcome them by name
2. Acknowledge their discharge date and diagnosis
3. Ask how they're feeling today
4. Ask if they're following their medication schedule
5. Offer to help with any questions

Keep it friendly, empathetic, and professional. 2-3 sentences max."""
        
        try:
            greeting = self.llm.simple_query(
                prompt=prompt,
                system_message=self.system_prompt,
                temperature=0.7  # Slightly higher for warmth
            )
            
            return greeting
        
        except Exception as e:
            # Fallback to template-based greeting
            return f"""Hi {self.patient_name}! 👋

I found your discharge report from {discharge_date} for {diagnosis}. 

How are you feeling today? Are you following your medication schedule?

I'm here to help with any questions about your recovery or discharge instructions."""
    
    def chat(self, user_message: str) -> Dict:
        """
        Process user message and generate response
        
        Args:
            user_message: User's message
        
        Returns:
            Dict with response and routing decision
        """
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Check if this is a medical query that needs Clinical Agent
        routing_decision = self._should_route_to_clinical(user_message)
        
        if routing_decision['route_to_clinical']:
            return {
                "response": routing_decision['handoff_message'],
                "route_to_clinical": True,
                "query": user_message,
                "patient_context": self._get_patient_context()
            }
        
        # Generate response as receptionist
        response = self._generate_response(user_message)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return {
            "response": response,
            "route_to_clinical": False
        }
    
    def _should_route_to_clinical(self, message: str) -> Dict:
        """Determine if query should be routed to Clinical Agent"""
        
        # Medical keywords that indicate need for clinical expertise
        medical_keywords = [
            'symptom', 'pain', 'swelling', 'bleeding', 'fever',
            'side effect', 'medication', 'treatment', 'diagnosis',
            'test result', 'lab', 'doctor', 'emergency', 'worried',
            'should i', 'is it normal', 'what if', 'concern'
        ]
        
        message_lower = message.lower()
        
        # Check for medical keywords
        has_medical_keyword = any(keyword in message_lower for keyword in medical_keywords)
        
        # Use LLM for more nuanced detection
        if has_medical_keyword or len(message) > 20:
            prompt = f"""Patient message: "{message}"

Is this a medical question that requires clinical expertise? Answer with just YES or NO.

Medical questions include: symptoms, side effects, treatment advice, medication questions, health concerns.
General questions include: appointment scheduling, general greetings, clarification of instructions."""
            
            try:
                llm_decision = self.llm.simple_query(
                    prompt=prompt,
                    temperature=0.1  # Low for classification
                )
                
                is_medical = 'yes' in llm_decision.lower()
            except:
                is_medical = has_medical_keyword
        else:
            is_medical = False
        
        if is_medical:
            return {
                "route_to_clinical": True,
                "handoff_message": "I understand this is a medical question. Let me connect you with our Clinical AI Agent who can provide detailed medical guidance based on your condition and the latest nephrology research. One moment please... 🏥"
            }
        
        return {
            "route_to_clinical": False,
            "handoff_message": None
        }
    
    def _generate_response(self, user_message: str) -> str:
        """Generate response as receptionist"""
        
        # Build context
        context = f"""Patient Information:
- Name: {self.patient_name}
- Diagnosis: {self.patient_data['primary_diagnosis']}
- Discharge Date: {self.patient_data['discharge_date']}
- Medications: {', '.join(self.patient_data['medications'][:3])}
- Dietary Restrictions: {self.patient_data['dietary_restrictions']}

Patient message: {user_message}

Respond as a friendly receptionist. Provide helpful information from their discharge report, but remind them to consult clinical AI or their doctor for medical advice."""
        
        try:
            response = self.llm.simple_query(
                prompt=context,
                system_message=self.system_prompt,
                temperature=0.7
            )
            
            return response
        
        except Exception as e:
            return f"I understand your question. For detailed medical guidance, I recommend speaking with our Clinical AI Agent or your healthcare provider. Is there anything else I can help you with regarding your discharge instructions?"
    
    def _get_patient_context(self) -> str:
        """Get patient context for Clinical Agent"""
        
        if not self.patient_data:
            return ""
        
        context = f"""Patient Context:
- Name: {self.patient_name}
- Primary Diagnosis: {self.patient_data['primary_diagnosis']}
- Secondary Diagnoses: {', '.join(self.patient_data['secondary_diagnoses'])}
- Current Medications: {', '.join(self.patient_data['medications'])}
- Lab Values: Creatinine {self.patient_data['lab_values']['creatinine']}, eGFR {self.patient_data['lab_values']['egfr']}
- Discharge Date: {self.patient_data['discharge_date']}
- Warning Signs to Watch: {self.patient_data['warning_signs']}
"""
        
        return context
    
    def get_patient_summary(self) -> str:
        """Get formatted patient summary"""
        
        if not self.patient_data:
            return "No patient data loaded"
        
        summary = f"""
📋 **Patient Summary: {self.patient_name}**

🏥 **Diagnosis:** {self.patient_data['primary_diagnosis']}
📅 **Discharge Date:** {self.patient_data['discharge_date']}

💊 **Medications:** ({len(self.patient_data['medications'])} total)
{chr(10).join(['  - ' + med for med in self.patient_data['medications'][:5]])}

🔬 **Lab Values:**
  - Creatinine: {self.patient_data['lab_values']['creatinine']} mg/dL
  - eGFR: {self.patient_data['lab_values']['egfr']} mL/min/1.73m²
  - Hemoglobin: {self.patient_data['lab_values']['hemoglobin']} g/dL

⚠️ **Warning Signs:** {self.patient_data['warning_signs']}

📞 **Follow-up:** {self.patient_data['follow_up']}
"""
        
        return summary


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def test_receptionist_agent():
    """Test Receptionist Agent"""
    
    print("="*70)
    print("TESTING RECEPTIONIST AGENT")
    print("="*70)
    
    agent = ReceptionistAgent()
    
    # Test 1: Initial greeting
    print("\n📝 Test 1: Initial Greeting")
    print("-"*70)
    greeting = agent.greet_patient()
    print(greeting)
    
    # Test 2: Process patient name
    print("\n\n📝 Test 2: Process Patient Name")
    print("-"*70)
    
    # Get a patient name from database
    db_tool = PatientDatabaseTool()
    patient_names = db_tool.get_all_patient_names()
    test_name = patient_names[0]
    
    print(f"Testing with patient: {test_name}")
    result = agent.process_patient_name(test_name)
    
    print(f"\nStatus: {result['status']}")
    print(f"Response:\n{result['response']}")
    
    # Test 3: General chat
    print("\n\n📝 Test 3: General Chat")
    print("-"*70)
    
    chat_result = agent.chat("Yes, I'm taking all my medications on time.")
    print(f"Route to Clinical: {chat_result['route_to_clinical']}")
    print(f"Response:\n{chat_result['response']}")
    
    # Test 4: Medical query (should route)
    print("\n\n📝 Test 4: Medical Query Routing")
    print("-"*70)
    
    medical_query = "I'm experiencing some swelling in my legs. Should I be worried?"
    chat_result = agent.chat(medical_query)
    
    print(f"Query: {medical_query}")
    print(f"Route to Clinical: {chat_result['route_to_clinical']}")
    print(f"Response:\n{chat_result['response']}")
    
    if chat_result['route_to_clinical']:
        print(f"\n📋 Patient Context for Clinical Agent:")
        print(chat_result['patient_context'])
    
    # Test 5: Patient summary
    print("\n\n📝 Test 5: Patient Summary")
    print("-"*70)
    print(agent.get_patient_summary())
    
    print("\n" + "="*70)
    print("✅ RECEPTIONIST AGENT TESTS COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    try:
        test_receptionist_agent()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

        