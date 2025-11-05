# 🏥 Post-Discharge Medical AI Assistant


> **An intelligent multi-agent AI system for post-discharge patient care powered by LangGraph, Groq LLM, and RAG (Retrieval-Augmented Generation)**


The **Post-Discharge Medical AI Assistant** is a sophisticated multi-agent conversational AI system designed to support patients during their post-discharge recovery period. Built with state-of-the-art technologies including LangGraph for agent orchestration and Groq's lightning-fast LLM inference, this system demonstrates how AI can enhance patient care through intelligent information retrieval and personalized medical guidance.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/LLM-Groq-green.svg)](https://groq.com/)
[![LangGraph](https://img.shields.io/badge/Framework-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)


##  Overview

This **Proof of Concept (POC)** system demonstrates a multi-agent AI architecture for post-discharge patient care in nephrology. It combines:

- **RAG (Retrieval Augmented Generation)** with a comprehensive nephrology textbook
- **Multi-Agent Orchestration** using LangGraph
- **Real-time Web Search** for latest medical research
- **Patient Data Management** with SQLite
- **Comprehensive Logging** of all interactions



##  Features

###  **Multi-Agent Architecture**

1. **Receptionist Agent**
   - Greets patients warmly
   - Retrieves discharge reports from database
   - Asks follow-up questions based on patient history
   - Routes medical queries to Clinical Agent

2. **Clinical AI Agent**
   - Answers medical questions using RAG
   - Searches 9706+ medical knowledge chunks
   - Uses web search for latest research
   - Provides evidence-based answers with citations

###  **RAG Implementation**

- **Knowledge Base**: Comprehensive Clinical Nephrology (1547 pages)
- **Vector Store**: ChromaDB with 9706 chunks
- **Embeddings**: HuggingFace (all-MiniLM-L6-v2)
- **Semantic Search**: Top-K retrieval with citations

###  **Web Search Integration**

- Tavily API for real-time medical research
- Automatic detection of queries needing latest info
- Clear source attribution

###  **Patient Data Management**

- 30+ dummy post-discharge reports
- SQLite database for efficient retrieval
- Patient context awareness in conversations

###  **Comprehensive Logging**

- Interaction logs (patient conversations)
- Agent decision logs (routing, tool usage)
- System logs (errors, performance)
- Structured JSON logs for analysis

---

##  System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
│                  (User Interface Layer)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LangGraph Orchestrator                         │
│           (Multi-Agent Coordination)                        │
└─────┬────────────────────────────────────┬─────────────────┘
      │                                    │
┌─────▼─────────────┐           ┌─────────▼────────────────┐
│ Receptionist Agent│           │   Clinical AI Agent      │
│                   │           │                          │
│ - Patient Greeting│           │ - Medical Q&A            │
│ - Data Retrieval  │           │ - RAG Search             │
│ - Query Routing   │           │ - Web Search             │
└─────┬─────────────┘           └──────────┬───────────────┘
      │                                    │
┌─────▼─────────────────────────────────────▼───────────────┐
│                    Agent Tools Layer                       │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐│
│  │   Patient    │  │     RAG      │  │   Web Search    ││
│  │   Database   │  │  Retriever   │  │     Tool        ││
│  └──────────────┘  └──────────────┘  └─────────────────┘│
└────────────────────────────────────────────────────────────┘
      │                     │                      │
┌─────▼──────┐    ┌────────▼────────┐    ┌───────▼────────┐
│  SQLite    │    │   ChromaDB      │    │  Tavily API    │
│  (30 pts)  │    │ (9706 chunks)   │    │ (Web Search)   │
└────────────┘    └─────────────────┘    └────────────────┘
```


## Usage

### **Run the Application**

```bash
streamlit run frontend/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

### **Using the System**

1. **Start Conversation**: System greets you
2. **Provide Name**: Enter patient name (e.g., "Adam King")
3. **Ask Questions**: 
   - General: "How should I take my medications?"
   - Medical: "I have leg swelling, is this normal?"
4. **Get Responses**: 
   - Receptionist handles general queries
   - Clinical Agent handles medical questions with RAG


##  Project Structure

```
post-discharge-ai-assistant/
├── README.md
├── requirements.txt
├── .env
├── config/
│   ├── __init__.py
│   └── settings.py                 # Configuration
├── data/
│   ├── patients/
│   │   ├── patients.json           # 30 patient reports
│   │   └── patients.db             # SQLite database
│   ├── reference_materials/
│   │   ├── comprehensive-clinical-nephrology.pdf
│   │   └── processed/
│   │       └── chunks.json         # Processed chunks
│   └── vector_store/
│       └── chroma_db/              # Vector embeddings
├── src/
│   ├── agents/
│   │   ├── receptionist_agent.py   # Receptionist
│   │   ├── clinical_agent.py       # Clinical expert
│   │   └── agent_tools.py          # Tools (DB, RAG, Search)
│   ├── data_preparation/
│   │   ├── patient_data_generator.py
│   │   └── pdf_processor.py
│   ├── llm/
│   │   └── groq_client.py          # Groq API wrapper
│   ├── orchestration/
│   │   └── multi_agent_graph.py    # LangGraph workflow
│   └── utils/
│       └── logger.py               # Logging system
├── frontend/
│   └── streamlit_app.py            # UI
└── logs/
    ├── interactions/
    ├── agent_decisions/
    └── system/
```


##  Important Notes

1. **Educational Purpose**: This system is for demonstration only
2. **Not Medical Advice**: Always consult healthcare professionals
3. **Dummy Data**: All patient data is fictional
4. **API Costs**: Groq and Tavily free tiers should be sufficient for POC

### Data Sources

- Nephrology reference materials (publicly available medical literature)
- Dummy patient data generated using Faker library


##  Contact

> **Project Maintainer :** [Atish Kumar Sharma – IIIT Lucknow]

- Email: atish.sharma7321@gmail.com
- LinkedIn: [Atish-Kr-Sharma](https://www.linkedin.com/in/atish-kr-sharma-85a2972a7/)
- GitHub: [Atish019](https://github.com/Atish019)


**Built with  using Groq, LangGraph, ChromaDB & Streamlit**
