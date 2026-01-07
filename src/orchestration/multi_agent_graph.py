"""
Multi-Agent Orchestration using LangGraph
Coordinates ReceptionistAgent and ClinicalAIAgent
"""
from typing import TypedDict, Optional, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from src.agents.clinical_agent import ClinicalAIAgent
from src.agents.agent_tools import get_patient_by_name
from src.utils.logger import log_system
# STATE DEFINITION
class AgentState(TypedDict):
    """Complete state for multi-agent conversation"""
    
    # Input
    message: str
    session_id: str
    message_count: int
    
    # Patient data
    patient_data: Optional[dict]
    patient_identified: bool
    # Routing
    route: Literal["greeting", "identification", "medical", "general", "end"]
    # Output
    response: dict
    # Metadata
    timestamp: str

# MEDICAL KEYWORDS FOR ROUTING
MEDICAL_KEYWORDS = [
    # Kidney-Specific
    "kidney", "kidneys", "renal", "nephrology", "dialysis", "transplant",
    "creatinine", "egfr", "urine", "urination", "urinating",
    "proteinuria", "hematuria", "albuminuria",
    # Common Symptoms

    "pain", "ache", "aching", "hurt", "hurting", "sore",
    "swelling", "swollen", "edema", "puffiness", "bloated", "bloating",
    "fever", "temperature", "chills", "hot", "cold sweats",
    "nausea", "vomiting", "vomit", "throw up", "throwing up",
    "dizziness", "dizzy", "lightheaded", "vertigo", "spinning",
    "weakness", "weak", "fatigue", "tired", "exhausted", "exhaustion",
    "headache", "head pain", "migraine",
    "shortness of breath", "breathing", "breathless", "dyspnea", "sob",
    "chest pain", "chest pressure", "chest tightness",
    # Vision & Sensory

    "blurry vision", "blurred", "vision", "seeing", "eyesight",
    "eyes", "eye", "burning eyes", "itchy eyes", "dry eyes",
    # Cardiovascular

    "blood pressure", "bp", "hypertension", "hypotension",
    "heart rate", "palpitations", "irregular heartbeat",
    
    # Gastrointestinal
    "stomach", "abdomen", "belly", "abdominal pain",
    "diarrhea", "constipation", "bowel", "stool",
    "appetite", "eating", "hungry",
    
    # Skin
    "rash", "itching", "itchy", "scratch", "scratching",
    "bruising", "bruise", "bleeding", "blood",
    "skin", "pale", "yellow", "jaundice",
    
    # Neurological
    "confusion", "confused", "memory", "forgetful",
    "numbness", "tingling", "pins and needles",
    "tremor", "shaking", "seizure",
    
    # Medications
    "medication", "medicine", "drug", "pill", "tablet",
    "prescription", "dose", "dosage", "dosing",
    "side effect", "side effects", "adverse", "reaction",
    
    # Lab & Clinical
    "lab", "labs", "test", "testing", "blood test",
    "result", "results", "report", "levels",
    "potassium", "sodium", "calcium", "phosphorus",
    "hemoglobin", "anemia", "albumin",
    
    # General Medical
    "infection", "infected", "pus", "discharge",
    "wound", "injury", "surgery", "operation",
    "doctor", "hospital", "clinic", "emergency",
    "symptom", "symptoms", "signs",
    
    # Urgency
    "severe", "serious", "emergency", "urgent", "immediately",
    "worse", "worsening", "getting worse", "not improving",
    
    # Treatment & Research
    "treatment", "therapy", "cure", "heal", "healing",
    "research", "study", "studies", "clinical trial",
    "latest", "new", "recent", "current", "update",
    "guidelines", "recommendations", "protocol",
    "breakthrough", "advancement", "discovery",
    
    # Query Patterns
    "what is", "what are", "what should", "what can",
    "how to", "how do", "how long", "how much",
    "when should", "when do", "when to",
    "why is", "why do", "why am",
    "should i", "can i", "may i",
    "is it normal", "is this normal", "normal to"
]
clinical_agent = ClinicalAIAgent()

def is_medical_query(message: str) -> bool:
    """Check if message contains medical keywords"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in MEDICAL_KEYWORDS)


def format_patient_details(patient: dict) -> str:
    """Format patient discharge details"""
    medications_list = "\n".join([f"   • {med}" for med in patient.get('medications', [])])
    secondary_dx = ", ".join(patient.get('secondary_diagnoses', []))
    
    lab_values = patient.get('lab_values', {})
    lab_text = f"""   • Creatinine: {lab_values.get('creatinine', 'N/A')} mg/dL
   • eGFR: {lab_values.get('egfr', 'N/A')} mL/min
   • Potassium: {lab_values.get('potassium', 'N/A')} mEq/L
   • Hemoglobin: {lab_values.get('hemoglobin', 'N/A')} g/dL"""
    
    return f"""Hi {patient['patient_name']}! I found your discharge report. Here are your details:

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

📅 Follow-up Appointment:
   {patient.get('follow_up', 'N/A')}

⚠️ Warning Signs to Watch For:
   {patient.get('warning_signs', 'N/A')}

📝 Discharge Instructions:
   {patient.get('discharge_instructions', 'N/A')}

---
How are you feeling today? Do you have any questions about your medications or symptoms?"""

# GRAPH NODES
def entry_node(state: AgentState) -> AgentState:
    """
    Entry node - determines conversation stage
    """
    log_system(f"[Entry Node] Message #{state['message_count']}: {state['message'][:50]}...")
    
    # Determine route based on conversation state
    if state["message_count"] == 1:
        state["route"] = "greeting"
    elif not state["patient_identified"]:
        state["route"] = "identification"
    else:
        # Check if medical or general query
        if is_medical_query(state["message"]):
            state["route"] = "medical"
        else:
            state["route"] = "general"
    
    log_system(f"[Entry Node] Route: {state['route']}")
    return state

def greeting_node(state: AgentState) -> AgentState:
    """
    Send initial greeting
    """
    log_system("[Greeting Node] Sending greeting")
    
    state["response"] = {
        "method": "greeting",
        "answer": "Hello! I'm your post-discharge care assistant. What's your name?",
        "patient_identified": False
    }
    
    state["route"] = "end"
    return state

def identification_node(state: AgentState) -> AgentState:
    """
    Identify patient by name
    """
    log_system(f"[Identification Node] Fetching patient: {state['message']}")
    
    patient = get_patient_by_name(state["message"])
    
    if "error" in patient:
        log_system("[Identification Node] Patient not found")
        state["response"] = {
            "method": "patient_identification_failed",
            "answer": patient["error"],
            "patient_identified": False
        }
    else:
        log_system(f"[Identification Node] Patient found: {patient['patient_name']}")
        state["patient_data"] = patient
        state["patient_identified"] = True
        
        state["response"] = {
            "method": "patient_identification",
            "answer": format_patient_details(patient),
            "patient_identified": True
        }
    state["route"] = "end"
    return state

def medical_node(state: AgentState) -> AgentState:
    """
    Handle medical queries via Clinical Agent
    """
    log_system(f"[Medical Node] Processing medical query")
    
    try:
        # Call clinical agent
        clinical_response = clinical_agent.answer_medical_query(state["message"])
        
        # Extract answer
        answer = clinical_response.get("answer", "")
        method = clinical_response.get("method", "unknown")
        
        # Add patient context
        if state["patient_data"]:
            diagnosis = state["patient_data"].get("primary_diagnosis", "N/A")
            answer += f"\n\n💡 **Your Current Diagnosis:** {diagnosis}"
        
        state["response"] = {
            "method": f"clinical_{method}",
            "answer": answer,
            "patient_identified": True
        }
        
        log_system(f"[Medical Node] Response via {method}")
    
    except Exception as e:
        log_system(f"[Medical Node] ERROR: {str(e)}")
        state["response"] = {
            "method": "error",
            "answer": (
                "I apologize, but I'm having trouble processing your medical query. "
                "Please try rephrasing or contact your healthcare provider.\n\n"
                "⚠️ This is for educational purposes only."
            ),
            "patient_identified": state["patient_identified"]
        }
    
    state["route"] = "end"
    return state

def general_node(state: AgentState) -> AgentState:
    """
    Handle general (non-medical) queries
    """
    log_system("[General Node] Handling general query")
    
    state["response"] = {
        "method": "general",
        "answer": (
            "Thank you for sharing that information. "
            "Please continue following your discharge instructions. "
            "If you have any medical concerns or symptoms, feel free to ask me!"
        ),
        "patient_identified": True
    }
    
    state["route"] = "end"
    return state

# BUILD LANGGRAPH
def build_graph():
    """Build and compile the LangGraph workflow"""
    
    log_system(" Building Multi-Agent Graph...")
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("entry", entry_node)
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("identification", identification_node)
    workflow.add_node("medical", medical_node)
    workflow.add_node("general", general_node)
    # Set entry point
    workflow.set_entry_point("entry")
    # Conditional routing from entry
    workflow.add_conditional_edges(
        "entry",
        lambda state: state["route"],
        {
            "greeting": "greeting",
            "identification": "identification",
            "medical": "medical",
            "general": "general"
        }
    )
    # All nodes go to END
    workflow.add_edge("greeting", END)
    workflow.add_edge("identification", END)
    workflow.add_edge("medical", END)
    workflow.add_edge("general", END)
    # Compile
    compiled_graph = workflow.compile()
    log_system(" Multi-Agent Graph compiled successfully")
    
    return compiled_graph

# Build graph on module load
multi_agent_graph = build_graph()

# PUBLIC INTERFACE
def process_message(message: str, session_state: dict) -> dict:
    """
    Process user message through the graph
    
    Args:
        message: User's input message
        session_state: Current session state
    
    Returns:
        dict: Response with updated state
    """
    log_system(f"[Graph] Processing: {message[:50]}...")
    
    # Build state
    state = AgentState(
        message=message,
        session_id=session_state.get("id", ""),
        message_count=session_state.get("message_count", 0) + 1,
        patient_data=session_state.get("patient_data"),
        patient_identified=session_state.get("patient_data") is not None,
        route="greeting",
        response={},
        timestamp=datetime.now().isoformat()
    )
    # Run through graph
    try:
        final_state = multi_agent_graph.invoke(state)
    except Exception as e:
        log_system(f"[Graph] ERROR: {str(e)}")
        final_state = state
        final_state["response"] = {
            "method": "error",
            "answer": "An error occurred. Please try again.",
            "patient_identified": state["patient_identified"]
        }
    
    log_system(f"[Graph] Complete. Method: {final_state['response'].get('method')}")
    
    # Return response
    return {
        "answer": final_state["response"]["answer"],
        "method": final_state["response"]["method"],
        "patient_data": final_state["patient_data"],
        "patient_identified": final_state["response"]["patient_identified"],
        "message_count": final_state["message_count"]
    }
