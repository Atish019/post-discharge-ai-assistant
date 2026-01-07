"""
Agent Tools: Helper functions for patient data retrieval
"""
import json
from pathlib import Path
from src.utils.logger import log_agent

# Path to patient data
PATIENTS_FILE = Path("data/patients/patients.json")

def get_patient_by_name(name: str) -> dict:
    """
    Retrieve patient discharge report by name
    
    Args:
        name: Patient's full name (e.g., "John Smith")
    
    Returns:
        dict: Patient data or error message
    """
    try:
        # Load patients data
        with open(PATIENTS_FILE, 'r', encoding='utf-8') as f:
            patients = json.load(f)
        
        # Search for patient (case-insensitive)
        name_lower = name.lower().strip()
        
        for patient in patients:
            if patient['patient_name'].lower() == name_lower:
                log_agent(f" Patient retrieved: {patient['patient_name']}")
                return patient
        
        # Patient not found
        log_agent(f" Patient not found: {name}")
        return {
            "error": f"I couldn't find a patient named '{name}' in our records. Please check the spelling or try another name."
        }
    
    except FileNotFoundError:
        log_agent(f"ERROR: Patients file not found at {PATIENTS_FILE}")
        return {
            "error": "Patient database is not available. Please contact support."
        }
    
    except Exception as e:
        log_agent(f"ERROR: {str(e)}")
        return {
            "error": "An error occurred while retrieving patient data."
        }