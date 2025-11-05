"""
Configuration Settings
Centralized configuration management with environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
(LOGS_DIR / "interactions").mkdir(exist_ok=True)
(LOGS_DIR / "agent_decisions").mkdir(exist_ok=True)
(LOGS_DIR / "system").mkdir(exist_ok=True)


# ============================================================================
# API KEYS
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")  # Optional

# Validation
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env file!")
if not TAVILY_API_KEY:
    print("⚠️  TAVILY_API_KEY not found - web search will be limited")


# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Groq Model Settings (Updated Nov 2024)
##GROQ_MODEL_NAME = "llama-3.3-70b-versatile"  # RECOMMENDED: Latest production model

GROQ_MODEL_NAME = "llama-3.1-8b-instant"  # Alternative for medical tasks
# Alternatives:
# "llama-3.1-8b-instant" (faster, smaller)
# "gemma2-9b-it" (good balance)
# "mixtral-8x7b-32768" (older but stable)

GROQ_TEMPERATURE = 0.3  # Low for medical accuracy
GROQ_MAX_TOKENS = 2048  # Response length
GROQ_TOP_P = 0.9


# ============================================================================
# EMBEDDINGS CONFIGURATION
# ============================================================================

# HuggingFace Embedding Model (Free)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
# Alternative: "BAAI/bge-small-en-v1.5" (better for medical)

EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2


# ============================================================================
# VECTOR STORE CONFIGURATION
# ============================================================================

VECTOR_DB_PATH = DATA_DIR / "vector_store" / "chroma_db"
VECTOR_DB_COLLECTION_NAME = "nephrology_knowledge"

# Retrieval settings
RAG_TOP_K = 5  # Number of chunks to retrieve
RAG_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score


# ============================================================================
# DATABASE CONFIGURATION

PATIENT_DB_PATH = DATA_DIR / "patients" / "patients.db"
PATIENT_JSON_PATH = DATA_DIR / "patients" / "patients.json"


# ============================================================================
# PDF PROCESSING CONFIGURATION
# ============================================================================

PDF_PATH = DATA_DIR / "reference_materials" / "comprehensive-clinical-nephrology.pdf"
PROCESSED_CHUNKS_DIR = DATA_DIR / "reference_materials" / "processed"

# Chunking settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Agent types
AGENT_TYPES = {
    "receptionist": "Receptionist Agent",
    "clinical": "Clinical AI Agent"
}

# Max conversation turns
MAX_CONVERSATION_TURNS = 20


# ============================================================================
# WEB SEARCH CONFIGURATION
# ============================================================================

# Tavily Search Settings
TAVILY_MAX_RESULTS = 3
TAVILY_SEARCH_DEPTH = "basic"  # or "advanced"


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"

# Log file paths
INTERACTION_LOG = LOGS_DIR / "interactions" / "interactions.log"
AGENT_LOG = LOGS_DIR / "agent_decisions" / "agent_decisions.log"
SYSTEM_LOG = LOGS_DIR / "system" / "system.log"


# ============================================================================
# FRONTEND CONFIGURATION
# ============================================================================

STREAMLIT_PAGE_TITLE = "Post-Discharge Medical AI Assistant"
STREAMLIT_PAGE_ICON = "🏥"
STREAMLIT_LAYOUT = "wide"


# ============================================================================
# MEDICAL DISCLAIMER
# ============================================================================

MEDICAL_DISCLAIMER = """
⚠️ **IMPORTANT MEDICAL DISCLAIMER**

This is an AI assistant for educational purposes only. The information provided 
should NOT be used as a substitute for professional medical advice, diagnosis, 
or treatment. 

**Always consult with qualified healthcare professionals for medical advice.**

This system uses AI technology which may produce errors or inaccuracies. 
All medical decisions should be made in consultation with your doctor.
"""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_config_summary():
    """Print configuration summary"""
    return f"""
Configuration Summary:
=====================
 Groq Model: {GROQ_MODEL_NAME}
 Embedding Model: {EMBEDDING_MODEL_NAME}
 Vector DB: {VECTOR_DB_PATH}
 Patient DB: {PATIENT_DB_PATH}
 PDF Path: {PDF_PATH}
 Logs Directory: {LOGS_DIR}

API Keys Status:
================
{'✅' if GROQ_API_KEY else '❌'} Groq API Key
{'✅' if TAVILY_API_KEY else '❌'} Tavily API Key
{'✅' if HUGGINGFACE_API_KEY else '⚠️ '} HuggingFace API Key (Optional)
"""


def validate_paths():
    """Validate all required paths exist"""
    issues = []
    
    if not PATIENT_DB_PATH.exists():
        issues.append(f"❌ Patient DB not found: {PATIENT_DB_PATH}")
    
    if not PDF_PATH.exists():
        issues.append(f"❌ PDF not found: {PDF_PATH}")
    
    if not VECTOR_DB_PATH.exists():
        issues.append(f"⚠️  Vector DB not initialized: {VECTOR_DB_PATH}")
    
    return issues


if __name__ == "__main__":
    print(get_config_summary())
    
    # Validate paths
    issues = validate_paths()
    if issues:
        print("\n  Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n All paths validated!")

