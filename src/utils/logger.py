"""
Comprehensive Logging System
Logs all interactions, agent decisions, and system events
"""

import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from loguru import logger
from config.settings import (
    LOGS_DIR,
    INTERACTION_LOG,
    AGENT_LOG,
    SYSTEM_LOG,
    LOG_LEVEL
)


# LOGGER CONFIGURATION

class SystemLogger:
    """Centralized logging system"""
    
    def __init__(self):
        """Initialize logging system"""
        
        # Ensure log directories exist
        LOGS_DIR.mkdir(exist_ok=True, parents=True)
        (LOGS_DIR / "interactions").mkdir(exist_ok=True)
        (LOGS_DIR / "agent_decisions").mkdir(exist_ok=True)
        (LOGS_DIR / "system").mkdir(exist_ok=True)
        
        # Configure loguru
        self._configure_loggers()
        
        print(" Logging system initialized")
    
    def _configure_loggers(self):
        """Configure different log files"""
        
        # Remove default logger
        logger.remove()
        
        # Add console logger (optional, for debugging)
        logger.add(
            sys.stdout,
            level=LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
            colorize=True
        )
        
        # Interaction logs (patient conversations)
        logger.add(
            INTERACTION_LOG,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            filter=lambda record: "interaction" in record["extra"]
        )
        
        # Agent decision logs (routing, tool usage)
        logger.add(
            AGENT_LOG,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            filter=lambda record: "agent" in record["extra"]
        )
        
        # System logs (errors, performance)
        logger.add(
            SYSTEM_LOG,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            filter=lambda record: "system" in record["extra"]
        )
    
    # INTERACTION LOGGING
    
    def log_user_message(
        self,
        patient_name: Optional[str],
        message: str,
        session_id: str
    ):
        """Log user message"""
        
        logger.bind(interaction=True).info(
            f"[USER] Session: {session_id} | Patient: {patient_name or 'Unknown'} | Message: {message}"
        )
    
    def log_agent_response(
        self,
        agent_type: str,
        response: str,
        session_id: str,
        patient_name: Optional[str] = None
    ):
        """Log agent response"""
        
        # Truncate long responses for log readability
        truncated_response = response[:200] + "..." if len(response) > 200 else response
        
        logger.bind(interaction=True).info(
            f"[{agent_type.upper()}] Session: {session_id} | Patient: {patient_name or 'Unknown'} | Response: {truncated_response}"
        )
    
    def log_conversation_start(self, session_id: str):
        """Log conversation start"""
        
        logger.bind(interaction=True).info(
            f"[START] New conversation started | Session: {session_id}"
        )
    
    def log_conversation_end(
        self,
        session_id: str,
        turn_count: int,
        patient_name: Optional[str] = None
    ):
        """Log conversation end"""
        
        logger.bind(interaction=True).info(
            f"[END] Conversation ended | Session: {session_id} | Patient: {patient_name or 'Unknown'} | Turns: {turn_count}"
        )
    
    # AGENT DECISION LOGGING
    
    def log_agent_handoff(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        session_id: str
    ):
        """Log agent handoff"""
        
        logger.bind(agent=True).info(
            f"[HANDOFF] {from_agent} → {to_agent} | Reason: {reason} | Session: {session_id}"
        )
    
    def log_patient_retrieval(
        self,
        patient_name: str,
        found: bool,
        session_id: str
    ):
        """Log patient data retrieval"""
        
        status = "SUCCESS" if found else "NOT_FOUND"
        logger.bind(agent=True).info(
            f"[DB_QUERY] Patient: {patient_name} | Status: {status} | Session: {session_id}"
        )
    
    def log_rag_retrieval(
        self,
        query: str,
        num_results: int,
        session_id: str
    ):
        """Log RAG retrieval"""
        
        logger.bind(agent=True).info(
            f"[RAG] Query: {query[:50]}... | Results: {num_results} | Session: {session_id}"
        )
    
    def log_web_search(
        self,
        query: str,
        num_results: int,
        session_id: str
    ):
        """Log web search"""
        
        logger.bind(agent=True).info(
            f"[WEB_SEARCH] Query: {query[:50]}... | Results: {num_results} | Session: {session_id}"
        )
    
    def log_tool_usage(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        success: bool,
        session_id: str
    ):
        """Log tool usage"""
        
        status = "SUCCESS" if success else "FAILED"
        logger.bind(agent=True).info(
            f"[TOOL] {tool_name} | Params: {json.dumps(parameters)} | Status: {status} | Session: {session_id}"
        )
    
    # SYSTEM LOGGING
    
    def log_system_event(self, event: str, details: Optional[Dict] = None):
        """Log system event"""
        
        message = f"[SYSTEM] {event}"
        if details:
            message += f" | Details: {json.dumps(details)}"
        
        logger.bind(system=True).info(message)
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        session_id: Optional[str] = None
    ):
        """Log error"""
        
        message = f"[ERROR] {error_type} | Message: {error_message}"
        if session_id:
            message += f" | Session: {session_id}"
        
        logger.bind(system=True).error(message)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        session_id: Optional[str] = None
    ):
        """Log performance metrics"""
        
        message = f"[PERFORMANCE] {operation} | Duration: {duration_ms:.2f}ms"
        if session_id:
            message += f" | Session: {session_id}"
        
        logger.bind(system=True).debug(message)
    
    # STRUCTURED LOGGING

    
    def log_structured_interaction(
        self,
        session_id: str,
        patient_name: Optional[str],
        agent_type: str,
        user_message: str,
        agent_response: str,
        routing_decision: Optional[str] = None,
        tools_used: Optional[list] = None,
        timestamp: Optional[str] = None
    ):
        """Log complete interaction in structured format"""
        
        timestamp = timestamp or datetime.now().isoformat()
        
        interaction_data = {
            "timestamp": timestamp,
            "session_id": session_id,
            "patient_name": patient_name,
            "agent_type": agent_type,
            "user_message": user_message,
            "agent_response": agent_response[:500],  # Truncate
            "routing_decision": routing_decision,
            "tools_used": tools_used or []
        }
        
        # Save to JSON log file
        json_log_file = LOGS_DIR / "interactions" / f"structured_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Read existing data
            if json_log_file.exists():
                with open(json_log_file, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            
            # Append new interaction
            data.append(interaction_data)
            
            # Write back
            with open(json_log_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.bind(system=True).error(f"Failed to write structured log: {e}")


# ============================================================================
# GLOBAL LOGGER INSTANCE
# ============================================================================

# Initialize global logger
system_logger = SystemLogger()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_logger() -> SystemLogger:
    """Get global logger instance"""
    return system_logger


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def test_logger():
    """Test logging system"""
    
    print("="*70)
    print("TESTING LOGGING SYSTEM")
    print("="*70 + "\n")
    
    logger_instance = get_logger()
    
    session_id = "test_session_001"
    patient_name = "John Doe"
    
    # Test 1: Conversation logging
    print("📝 Test 1: Conversation Logging")
    print("-"*70)
    
    logger_instance.log_conversation_start(session_id)
    logger_instance.log_user_message(patient_name, "Hello, I need help", session_id)
    logger_instance.log_agent_response("receptionist", "Hi John! How can I help?", session_id, patient_name)
    logger_instance.log_conversation_end(session_id, 5, patient_name)
    
    print("✅ Logged conversation flow\n")
    
    # Test 2: Agent decision logging
    print("📝 Test 2: Agent Decision Logging")
    print("-"*70)
    
    logger_instance.log_patient_retrieval(patient_name, True, session_id)
    logger_instance.log_rag_retrieval("What is CKD?", 5, session_id)
    logger_instance.log_web_search("latest CKD treatment", 3, session_id)
    logger_instance.log_agent_handoff("receptionist", "clinical", "Medical query detected", session_id)
    
    print("✅ Logged agent decisions\n")
    
    # Test 3: System logging
    print("📝 Test 3: System Logging")
    print("-"*70)
    
    logger_instance.log_system_event("Application started", {"version": "1.0.0"})
    logger_instance.log_error("Database", "Connection timeout", session_id)
    logger_instance.log_performance("RAG retrieval", 245.5, session_id)
    
    print("✅ Logged system events\n")
    
    # Test 4: Structured logging
    print("📝 Test 4: Structured Logging")
    print("-"*70)
    
    logger_instance.log_structured_interaction(
        session_id=session_id,
        patient_name=patient_name,
        agent_type="clinical",
        user_message="What are the symptoms of CKD?",
        agent_response="CKD symptoms include fatigue, swelling, and changes in urination...",
        routing_decision="clinical",
        tools_used=["rag_retrieval", "citation_generator"]
    )
    
    print("✅ Logged structured interaction\n")
    
    # Show log file locations
    print("\n" + "="*70)
    print("LOG FILE LOCATIONS")
    print("="*70)
    print(f"Interactions: {INTERACTION_LOG}")
    print(f"Agent Decisions: {AGENT_LOG}")
    print(f"System Events: {SYSTEM_LOG}")
    print(f"Structured Logs: {LOGS_DIR / 'interactions' / 'structured_*.json'}")
    
    print("\n✅ LOGGING SYSTEM TEST COMPLETE!")


if __name__ == "__main__":
    try:
        test_logger()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

       