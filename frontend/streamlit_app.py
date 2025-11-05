"""
Post-Discharge Medical AI Assistant - Streamlit Frontend
Multi-Agent System with LangGraph Integration
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.orchestration.multi_agent_graph import MultiAgentOrchestrator
from src.utils.logger import get_logger

# Page Configuration
st.set_page_config(
    page_title="Post-Discharge AI Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logger using existing function
try:
    app_logger = get_logger()
    session_id = str(uuid.uuid4())[:8]
except Exception as e:
    st.error(f"Logger initialization failed: {e}")
    app_logger = None
    session_id = "fallback"

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #17becf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 1rem;
    }
    
    .disclaimer-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
        font-size: 0.9rem;
    }
    
    .patient-info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 5px solid #17a2b8;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .agent-badge {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .receptionist-badge {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 1px solid #28a745;
    }
    
    .clinical-badge {
        background: linear-gradient(135deg, #cce5ff 0%, #b8daff 100%);
        color: #004085;
        border: 1px solid #007bff;
    }
    
    .stat-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #dee2e6;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
def initialize_session_state():
    """Initialize all session state variables"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.orchestrator = None
        st.session_state.messages = []
        st.session_state.agent_state = None
        st.session_state.conversation_count = 0
        st.session_state.patient_loaded = False
        st.session_state.clinical_queries = 0
        st.session_state.session_id = session_id
        
        if app_logger:
            app_logger.log_conversation_start(session_id)

initialize_session_state()

# SYSTEM INITIALIZATION 
@st.cache_resource(show_spinner=False)
def load_orchestrator():
    """Load multi-agent orchestrator"""
    try:
        if app_logger:
            app_logger.log_system_event("Loading Multi-Agent Orchestrator", {"session": session_id})
        
        orchestrator = MultiAgentOrchestrator()
        
        if app_logger:
            app_logger.log_system_event("Orchestrator loaded successfully", {"session": session_id})
        
        return orchestrator, None
    except Exception as e:
        error_msg = f"Failed to initialize system: {str(e)}"
        if app_logger:
            app_logger.log_error("OrchestratorInit", error_msg, session_id)
        return None, error_msg

# ==================== HEADER ====================
st.markdown('<div class="main-header">🏥 Post-Discharge Medical AI Assistant</div>', unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer-box">
    ⚠️ <strong>Medical Disclaimer:</strong> This is an AI assistant for educational purposes only. 
    Always consult your healthcare provider for personalized medical advice. This is a POC system.
</div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/hospital.png", width=80)
    st.title("System Dashboard")
    
    st.subheader("🔧 System Status")
    
    if not st.session_state.initialized:
        with st.spinner("🔄 Initializing AI System..."):
            st.info("Loading AI models, vector database, and agent tools...")
            orchestrator, error = load_orchestrator()
            
            if orchestrator:
                st.session_state.orchestrator = orchestrator
                st.session_state.initialized = True
                st.success(" System Ready!")
                st.balloons()
            else:
                st.error(f" Initialization Failed:\n{error}")
                st.stop()
    else:
        st.success(" System Online")
        st.caption(f"Session: {st.session_state.session_id}")
    
    st.divider()
    
    # ========== PATIENT INFO ==========
    st.subheader("👤 Patient Information")
    
    if st.session_state.patient_loaded and st.session_state.agent_state:
        patient_name = st.session_state.agent_state.get("patient_name")
        patient_context = st.session_state.agent_state.get("patient_context", "")
        
        if patient_name:
            st.markdown(f"""
            <div class="patient-info-box">
                <h4 style="margin-top:0;">📋 {patient_name}</h4>
                <p><strong>Status:</strong> Identified ✅</p>
            </div>
            """, unsafe_allow_html=True)
            
            if patient_context:
                with st.expander("📋 Patient Context", expanded=False):
                    st.text(patient_context)
            
            with st.expander("📊 Conversation Details", expanded=False):
                state = st.session_state.agent_state
                st.write(f"**Total Turns:** {state.get('turn_count', 0)}")
                st.write(f"**Patient Identified:** {'Yes ✅' if state.get('patient_identified') else 'No ❌'}")
                st.write(f"**Current Agent:** {state.get('current_agent', 'Unknown').title()}")
        else:
            st.info("Patient data loading...")
    else:
        st.info("👋 Enter patient name to load records")
    
    st.divider()
    
    # ========== STATISTICS ==========
    st.subheader("📊 Session Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(st.session_state.messages)}</div>
            <div class="stat-label">Messages</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.conversation_count}</div>
            <div class="stat-label">Interactions</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption(f"🏥 Clinical Queries: {st.session_state.clinical_queries}")
    
    st.divider()
    
    # ========== CONTROLS ==========
    st.subheader("⚙️ Controls")
    
    if st.button("🔄 New Conversation", type="secondary", use_container_width=True):
        if app_logger:
            patient_name = None
            if st.session_state.agent_state:
                patient_name = st.session_state.agent_state.get("patient_name")
            app_logger.log_conversation_end(
                st.session_state.session_id, 
                st.session_state.conversation_count,
                patient_name
            )
        
        st.session_state.messages = []
        st.session_state.agent_state = None
        st.session_state.patient_loaded = False
        st.session_state.conversation_count = 0
        st.session_state.clinical_queries = 0
        st.session_state.session_id = str(uuid.uuid4())[:8]
        
        if app_logger:
            app_logger.log_conversation_start(st.session_state.session_id)
        
        st.success("✅ Conversation cleared!")
        st.rerun()
    
    if st.button("📥 Download Chat History", type="primary", use_container_width=True):
        if st.session_state.messages:
            chat_history = {
                "timestamp": datetime.now().isoformat(),
                "session_id": st.session_state.session_id,
                "patient": st.session_state.agent_state.get("patient_name", "Unknown") if st.session_state.agent_state else "N/A",
                "messages": st.session_state.messages
            }
            st.download_button(
                label="💾 Save as JSON",
                data=json.dumps(chat_history, indent=2),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("No chat history to download")
    
    st.divider()
    
    st.caption("🤖 **Technology Stack**")
    st.caption("• LLM: Groq (Llama 3.1)")
    st.caption("• Framework: LangGraph")
    st.caption("• Vector DB: ChromaDB")
    st.caption("• Web Search: Tavily")

# ==================== CHAT INTERFACE ====================
st.subheader("💬 Chat Interface")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant" and "agent" in message:
            agent_name = message["agent"]
            if agent_name == "receptionist":
                st.markdown(
                    '<span class="agent-badge receptionist-badge">👔 Receptionist Agent</span>', 
                    unsafe_allow_html=True
                )
            elif agent_name == "clinical":
                st.markdown(
                    '<span class="agent-badge clinical-badge">🏥 Clinical AI Agent</span>', 
                    unsafe_allow_html=True
                )

# Initial greeting
if len(st.session_state.messages) == 0:
    greeting = """👋 **Hello! Welcome to the Post-Discharge Care Assistant.**

I'm here to help you with your post-discharge care. To get started, please tell me your name so I can retrieve your discharge records.

**Example:** "My name is Adam King" or just "Adam King"
    """
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": greeting,
        "agent": "receptionist",
        "timestamp": datetime.now().isoformat()
    })
    
    with st.chat_message("assistant"):
        st.markdown(greeting)
        st.markdown(
            '<span class="agent-badge receptionist-badge">👔 Receptionist Agent</span>', 
            unsafe_allow_html=True
        )

# Chat input
if prompt := st.chat_input("Type your message here...", key="chat_input"):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Log user message
    if app_logger:
        patient_name = None
        if st.session_state.agent_state and st.session_state.agent_state.get("patient_name"):
            patient_name = st.session_state.agent_state["patient_name"]
        app_logger.log_user_message(patient_name, prompt, st.session_state.session_id)
    
    # Process message
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                start_time = datetime.now()
                
                # Initialize state if None
                if st.session_state.agent_state is None:
                    init_result = st.session_state.orchestrator.start_conversation()
                    st.session_state.agent_state = init_result["state"]
                
                # Call orchestrator
                result = st.session_state.orchestrator.process_message(
                    user_message=prompt,
                    state=st.session_state.agent_state
                )
                
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                response = result.get("response", "I apologize, but I couldn't process that request.")
                agent_name = result.get("agent", "system")
                new_state = result.get("state", {})
                
                # Update state
                st.session_state.agent_state = new_state
                st.session_state.conversation_count += 1
                
                # Check patient identified
                if new_state.get("patient_identified") and not st.session_state.patient_loaded:
                    st.session_state.patient_loaded = True
                    if app_logger:
                        app_logger.log_patient_retrieval(
                            new_state.get("patient_name", "Unknown"),
                            True,
                            st.session_state.session_id
                        )
                
                # Track clinical queries
                if agent_name == "clinical":
                    st.session_state.clinical_queries += 1
                
                # Display response
                st.markdown(response)
                
                # Show badge
                if agent_name == "receptionist":
                    st.markdown(
                        '<span class="agent-badge receptionist-badge">👔 Receptionist Agent</span>', 
                        unsafe_allow_html=True
                    )
                elif agent_name == "clinical":
                    st.markdown(
                        '<span class="agent-badge clinical-badge">🏥 Clinical AI Agent</span>', 
                        unsafe_allow_html=True
                    )
                
                # Save message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Log
                if app_logger:
                    app_logger.log_agent_response(
                        agent_name,
                        response,
                        st.session_state.session_id,
                        new_state.get("patient_name")
                    )
                    app_logger.log_performance(
                        f"{agent_name}_processing",
                        duration_ms,
                        st.session_state.session_id
                    )
                
            except Exception as e:
                error_msg = f"❌ **System Error:**\n\n{str(e)}\n\nPlease try again."
                st.error(error_msg)
                
                if app_logger:
                    app_logger.log_error("MessageProcessing", str(e), st.session_state.session_id)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "agent": "error",
                    "timestamp": datetime.now().isoformat()
                })

# ==================== FOOTER ====================
st.divider()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 0.85rem; padding: 1rem;">
        <p style="margin: 0.5rem 0;">
            🏥 <strong>Post-Discharge Medical AI Assistant</strong>
        </p>
        <p style="margin: 0.5rem 0;">
            POC Assignment for <strong>DataSmith AI</strong> | GenAI Intern Role
        </p>
        <p style="margin: 0.5rem 0;">
            Built with LangGraph • Groq LLM • ChromaDB • Streamlit
        </p>
        <p style="margin: 0.5rem 0; font-size: 0.75rem;">
            Free & Open Source Architecture
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==================== HELP SECTION ====================
with st.expander("💡 How to Use This Assistant", expanded=False):
    st.markdown("""
    ### Getting Started
    
    1. **Enter Your Name**: Start by providing your name to retrieve discharge records
       - Example: "My name is Adam King"
    
    2. **General Questions**: Ask about medications, diet, or follow-up
       - Example: "What medications am I taking?"
    
    3. **Medical Queries**: Ask specific medical questions
       - Example: "I have swelling in my legs, is this normal?"
       - System will connect you with Clinical AI Agent
    
    4. **Latest Research**: Ask about recent medical studies
       - Example: "What's the latest research on SGLT2 inhibitors?"
    
    ### Tips
    
    - Be specific in your questions
    - Mention symptoms clearly
    - Ask one question at a time
    - Always follow up with your healthcare provider
    
    ### Agent Roles
    
    - **👔 Receptionist Agent**: Patient data retrieval and general queries
    - **🏥 Clinical AI Agent**: Medical questions using nephrology knowledge + web search
    """)
# MAIN APP


def main():
    """Main application entry point"""
    
if __name__ == "__main__":
    main()

    