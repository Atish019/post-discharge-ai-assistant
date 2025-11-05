"""
Multi-Agent Orchestration using LangGraph
Coordinates Receptionist and Clinical agents
"""

import sys
from pathlib import Path
from typing import TypedDict, Annotated, Literal
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END
from src.agents.receptionist_agent import ReceptionistAgent
from src.agents.clinical_agent import ClinicalAgent


# ============================================================================
# STATE DEFINITION
# ============================================================================

class ConversationState(TypedDict):
    """State structure for conversation flow"""
    
    # User inputs
    user_message: str
    
    # Patient identification
    patient_name: str | None
    patient_identified: bool
    
    # Conversation flow
    current_agent: Literal["receptionist", "clinical", "end"]
    conversation_history: list[dict]
    
    # Agent responses
    receptionist_response: str | None
    clinical_response: str | None
    
    # Patient context
    patient_context: str | None
    
    # Routing decisions
    route_to_clinical: bool
    conversation_complete: bool
    
    # Metadata
    timestamp: str
    turn_count: int


# ============================================================================
# MULTI-AGENT ORCHESTRATOR
# ============================================================================

class MultiAgentOrchestrator:
    """
    Orchestrates conversation between Receptionist and Clinical agents
    """
    
    def __init__(self):
        """Initialize orchestrator with agents"""
        
        print("🔄 Initializing Multi-Agent Orchestrator...")
        
        # Initialize agents
        self.receptionist = ReceptionistAgent()
        self.clinical = ClinicalAgent()
        
        # Build state graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(
            checkpointer=None,
            debug=False
        )
        
        print("✅ Multi-Agent Orchestrator ready!\n")
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        
        # Create graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes (agent functions)
        workflow.add_node("receptionist", self._receptionist_node)
        workflow.add_node("clinical", self._clinical_node)
        workflow.add_node("end", self._end_node)
        
        # Set entry point
        workflow.set_entry_point("receptionist")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "receptionist",
            self._route_after_receptionist,
            {
                "clinical": "clinical",
                "receptionist": "receptionist",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "clinical",
            self._route_after_clinical,
            {
                "receptionist": "receptionist",
                "clinical": "clinical",
                "end": "end"
            }
        )
        
        workflow.add_edge("end", END)
        
        return workflow
    
    # ========================================================================
    # NODE FUNCTIONS
    # ========================================================================
    
    def _receptionist_node(self, state: ConversationState) -> ConversationState:
        """Receptionist Agent node"""
        
        print("🏥 Receptionist Agent processing...")
        
        user_msg = state["user_message"]
        
        # Check if patient is identified
        if not state["patient_identified"]:
            # Try to process name
            result = self.receptionist.process_patient_name(user_msg)
            
            if result["status"] == "success":
                state["patient_identified"] = True
                state["patient_name"] = self.receptionist.patient_name
                state["patient_context"] = self.receptionist._get_patient_context()
                state["receptionist_response"] = result["response"]
            else:
                state["receptionist_response"] = result["response"]
        
        else:
            # Patient identified, handle conversation
            chat_result = self.receptionist.chat(user_msg)
            
            state["receptionist_response"] = chat_result["response"]
            state["route_to_clinical"] = chat_result.get("route_to_clinical", False)
            
            if state["route_to_clinical"]:
                state["patient_context"] = chat_result.get("patient_context", "")
        
        # Update conversation history
        state["conversation_history"].append({
            "agent": "receptionist",
            "message": state["receptionist_response"],
            "timestamp": datetime.now().isoformat()
        })
        
        state["turn_count"] += 1
        
        return state
    
    def _clinical_node(self, state: ConversationState) -> ConversationState:
        """Clinical Agent node"""
        
        print("⚕️  Clinical Agent processing...")
        
        # Set patient context
        if state["patient_context"]:
            self.clinical.set_patient_context(state["patient_context"])
        
        # Process medical query
        user_query = state["user_message"]
        
        # Check if query needs web search
        use_web = any(keyword in user_query.lower() for keyword in 
                     ["latest", "recent", "new", "current", "2024", "2025"])
        
        response = self.clinical.answer_medical_query(
            query=user_query,
            use_web_search=use_web
        )
        
        # Format response with sources
        formatted_response = self.clinical.format_response_with_sources(response)
        
        state["clinical_response"] = formatted_response
        
        # Update conversation history
        state["conversation_history"].append({
            "agent": "clinical",
            "message": formatted_response,
            "timestamp": datetime.now().isoformat(),
            "rag_sources": len(response["rag_sources"]),
            "web_sources": len(response["web_sources"])
        })
        
        state["turn_count"] += 1
        
        # Reset routing flag
        state["route_to_clinical"] = False
        
        return state
    
    def _end_node(self, state: ConversationState) -> ConversationState:
        """End conversation node"""
        
        print("✅ Conversation ended")
        state["conversation_complete"] = True
        return state
    
    # ========================================================================
    # ROUTING FUNCTIONS
    # ========================================================================
    
    def _route_after_receptionist(self, state: ConversationState) -> str:
        """Decide next agent after receptionist"""
        
        # Check if should route to clinical
        if state["route_to_clinical"]:
            return "clinical"
        
        # After response, wait for new user input (end this turn)
        return "end"
    
    def _route_after_clinical(self, state: ConversationState) -> str:
        """Decide next agent after clinical"""
        
        # After clinical answer, mark that we need new user input
        # Don't loop back automatically
        return "end"
    
    # ========================================================================
    # PUBLIC INTERFACE
    # ========================================================================
    
    def start_conversation(self) -> dict:
        """Start new conversation"""
        
        # Initialize state
        initial_state: ConversationState = {
            "user_message": "",
            "patient_name": None,
            "patient_identified": False,
            "current_agent": "receptionist",
            "conversation_history": [],
            "receptionist_response": None,
            "clinical_response": None,
            "patient_context": None,
            "route_to_clinical": False,
            "conversation_complete": False,
            "timestamp": datetime.now().isoformat(),
            "turn_count": 0
        }
        
        # Get initial greeting
        greeting = self.receptionist.greet_patient()
        
        initial_state["receptionist_response"] = greeting
        initial_state["conversation_history"].append({
            "agent": "receptionist",
            "message": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "response": greeting,
            "state": initial_state
        }
    
    def process_message(self, user_message: str, state: ConversationState) -> dict:
        """
        Process user message through agent workflow
        
        Args:
            user_message: User's input
            state: Current conversation state
        
        Returns:
            Dict with response and updated state
        """
        
        # Update state with new message
        state["user_message"] = user_message
        state["conversation_history"].append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Reset routing flags for new message
        state["route_to_clinical"] = False
        state["conversation_complete"] = False
        
        # Run through graph with recursion limit
        try:
            result = self.app.invoke(
                state,
                config={"recursion_limit": 10}  # Limit recursion
            )
        except Exception as e:
            print(f"⚠️  Graph execution error: {e}")
            # Return last valid state
            result = state
            result["receptionist_response"] = "I apologize for the confusion. Could you please rephrase your question?"
        
        # Get response (from either receptionist or clinical)
        response = result.get("clinical_response") or result.get("receptionist_response")
        
        return {
            "response": response,
            "state": result,
            "agent": "clinical" if result.get("clinical_response") else "receptionist"
        }
    
    def get_conversation_summary(self, state: ConversationState) -> str:
        """Get formatted conversation summary"""
        
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║             CONVERSATION SUMMARY                               ║
╚════════════════════════════════════════════════════════════════╝

Patient: {state['patient_name'] or 'Not identified'}
Total Turns: {state['turn_count']}
Started: {state['timestamp']}

Conversation History:
"""
        
        for i, entry in enumerate(state['conversation_history'], 1):
            agent = entry.get('agent', entry.get('role', 'unknown'))
            msg = entry['message'][:100] + "..." if len(entry['message']) > 100 else entry['message']
            summary += f"\n{i}. [{agent.upper()}] {msg}\n"
        
        return summary


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def test_orchestrator():
    """Test multi-agent orchestration"""
    
    print("="*70)
    print("TESTING MULTI-AGENT ORCHESTRATOR")
    print("="*70 + "\n")
    
    # Initialize orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Start conversation
    print("📝 Starting Conversation")
    print("-"*70)
    
    start = orchestrator.start_conversation()
    print(f"Bot: {start['response'][:200]}...\n")
    
    state = start['state']
    
    # Simulate conversation flow (one message at a time)
    test_messages = [
        ("User provides name", "Adam King"),
        ("User confirms medication", "Yes, I'm taking my medications regularly"),
        ("User asks medical question", "I'm experiencing some swelling in my legs. Is this normal?")
    ]
    
    for i, (description, msg) in enumerate(test_messages, 1):
        print(f"\n{'='*70}")
        print(f"Turn {i}: {description}")
        print(f"{'='*70}")
        print(f"User: {msg}\n")
        
        result = orchestrator.process_message(msg, state)
        state = result['state']
        
        agent_type = result['agent'].upper()
        response = result['response']
        
        # Truncate long responses
        display_response = response[:300] + "..." if len(response) > 300 else response
        
        print(f"🤖 Agent: {agent_type}")
        print(f"Response: {display_response}\n")
        
        if result['agent'] == 'clinical':
            print("💊 [Clinical Agent provided medical guidance with RAG]")
    
    # Print summary
    print("\n" + "="*70)
    print("✅ ORCHESTRATOR TEST COMPLETE!")
    print("="*70)
    print(f"\nTotal Turns: {state['turn_count']}")
    print(f"Patient: {state['patient_name']}")
    print(f"Interactions Logged: {len(state['conversation_history'])}")
    
    return state


if __name__ == "__main__":
    try:
        test_orchestrator()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


       