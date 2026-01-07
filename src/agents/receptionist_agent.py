"""
Receptionist Agent: Handles patient greeting, data retrieval, and query routing.
"""
from typing import Dict, Optional
from src.agents.agent_tools import get_patient_by_name
from src.agents.clinical_agent import ClinicalAIAgent
from src.utils.logger import log_agent


class ReceptionistAgent:
    """
    Receptionist Agent handles:
    - Patient greeting and identification
    - Discharge report retrieval
    - Query routing to Clinical AI Agent
    """
    
    # Medical keywords for query routing
    MEDICAL_KEYWORDS = [
        "pain", "swelling", "fever", "urine", "blood pressure",
        "shortness of breath", "infection", "medication", "medicine",
        "latest", "research", "guidelines", "treatment", "symptom",
        "side effect", "dosage", "prescription", "kidney", "dialysis"
    ]
    
    def __init__(self):
        """Initialize the receptionist agent with clinical agent."""
        self.clinical_agent = ClinicalAIAgent()
        log_agent("ReceptionistAgent initialized")
    
    def greet(self) -> str:
        """Generate greeting message for new patients."""
        log_agent("Receptionist: Sending greeting")
        return "Hello! I'm your post-discharge care assistant. What's your name?"
    
    def fetch_patient_data(self, name: str) -> Dict:
        """
        Fetch patient discharge report by name and format detailed response.
        
        Args:
            name: Patient's name
            
        Returns:
            Dict containing patient data or error message
        """
        log_agent(f"Receptionist: Fetching patient data for '{name}'")
        
        patient = get_patient_by_name(name)
        
        if "error" in patient:
            log_agent(f"Receptionist: Patient not found - {name}")
            return {
                "success": False,
                "message": patient["error"]
            }
        
        log_agent(f"Receptionist: Patient data retrieved successfully for '{name}'")
        
        # Format detailed patient response
        response_message = self._format_patient_details(patient)
        
        return {
            "success": True,
            "patient_data": patient,
            "message": response_message
        }
    
    def _format_patient_details(self, patient: dict) -> str:
        """
        Format patient discharge details into readable message.
        
        Args:
            patient: Patient data dictionary
            
        Returns:
            Formatted string with patient details
        """
        # Format medications list
        medications_list = "\n".join([f"   • {med}" for med in patient.get('medications', [])])
        
        # Format secondary diagnoses
        secondary_dx = ", ".join(patient.get('secondary_diagnoses', []))
        
        # Format lab values
        lab_values = patient.get('lab_values', {})
        lab_text = f"""   • Creatinine: {lab_values.get('creatinine', 'N/A')} mg/dL
   • eGFR: {lab_values.get('egfr', 'N/A')} mL/min
   • Potassium: {lab_values.get('potassium', 'N/A')} mEq/L
   • Hemoglobin: {lab_values.get('hemoglobin', 'N/A')} g/dL"""
        
        # Build complete message
        message = f"""Hi {patient['patient_name']}! I found your discharge report. Here are your details:

📋 **DISCHARGE SUMMARY**

👤 Patient Information:
   • Name: {patient['patient_name']}
   • ID: {patient['patient_id']}
   • Gender: {patient.get('gender', 'N/A')}
   • Date of Birth: {patient.get('date_of_birth', 'N/A')}

🏥 Hospital Stay:
   • Admission Date: {patient.get('admission_date', 'N/A')}
   • Discharge Date: {patient.get('discharge_date', 'N/A')}
   • Attending Physician: {patient.get('attending_physician', 'N/A')}

🩺 Diagnosis:
   • Primary: {patient.get('primary_diagnosis', 'N/A')}
   • Secondary: {secondary_dx if secondary_dx else 'None'}

💊 Medications Prescribed:
{medications_list}

🔬 Recent Lab Results:
{lab_text}

🍽️ Dietary Restrictions:
   {patient.get('dietary_restrictions', 'N/A')}

📅 **Follow-up Appointment:**
   {patient.get('follow_up', 'N/A')}

⚠️ **Warning Signs to Watch For:**
   {patient.get('warning_signs', 'N/A')}

📝 **Discharge Instructions:**
   {patient.get('discharge_instructions', 'N/A')}

---

How are you feeling today? Do you have any questions about your medications or symptoms?"""
        
        return message
    
    def _is_medical_query(self, message: str) -> bool:
        """
        Determine if the query is medical-related.
        
        Args:
            message: User's message
            
        Returns:
            True if medical query, False otherwise
        """
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.MEDICAL_KEYWORDS)
    
    def route_query(self, message: str, patient_data: Optional[Dict] = None) -> Dict:
        """
        Route user query to appropriate handler.
        
        Args:
            message: User's message
            patient_data: Patient's discharge data (optional)
            
        Returns:
            Response dictionary with method and answer
        """
        log_agent(f"Receptionist: Routing query - '{message[:50]}...'")
        
        # Check if it's a medical query
        if self._is_medical_query(message):
            log_agent("Receptionist: Identified as medical query, routing to Clinical Agent")
            
            try:
                # Call clinical agent (returns dict)
                clinical_response = self.clinical_agent.answer_medical_query(message)
                
                # Extract answer string from dict
                answer = clinical_response.get("answer", "")
                method = clinical_response.get("method", "unknown")
                sources = clinical_response.get("sources", "")
                
                # Add patient context if available
                if patient_data:
                    patient_context = f"\n\n💡 **Your Current Diagnosis:** {patient_data.get('primary_diagnosis', 'N/A')}"
                    answer = answer + patient_context
                
                log_agent(f"Receptionist: Clinical agent responded via {method}")
                
                return {
                    "method": f"clinical_{method}",
                    "answer": answer,
                    "sources": sources,
                    "routed_to": "clinical_agent"
                }
            
            except Exception as e:
                log_agent(f"Receptionist: Error in clinical agent - {str(e)}")
                return {
                    "method": "error",
                    "answer": (
                        "I apologize, but I'm having trouble processing your medical query. "
                        "Please try rephrasing or contact your healthcare provider directly.\n\n"
                        "⚠️ This is for educational purposes only and does not replace professional medical advice."
                    ),
                    "error": str(e)
                }
        
        # Handle general queries
        log_agent("Receptionist: Handling as general query")
        
        return {
            "method": "general",
            "answer": (
                "Thank you for sharing that information. "
                "Please continue following your discharge instructions. "
                "If you have any medical concerns or symptoms, feel free to ask me!"
            )
        }