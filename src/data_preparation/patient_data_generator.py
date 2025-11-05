"""
Patient Data Generator
Generates 25+ realistic dummy post-discharge patient reports for nephrology cases
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker
import sqlite3
from pathlib import Path

# Initialize Faker
fake = Faker()

# Nephrology-specific data
DIAGNOSES = [
    "Chronic Kidney Disease Stage 3",
    "Chronic Kidney Disease Stage 4",
    "Acute Kidney Injury",
    "Diabetic Nephropathy",
    "Hypertensive Nephropathy",
    "Glomerulonephritis",
    "Polycystic Kidney Disease",
    "Nephrotic Syndrome",
    "IgA Nephropathy",
    "Lupus Nephritis",
    "Kidney Stone Disease",
    "Urinary Tract Infection with AKI",
]

MEDICATIONS = {
    "CKD": ["Lisinopril 10mg daily", "Furosemide 20mg twice daily", "Sodium bicarbonate 650mg TID"],
    "HTN": ["Amlodipine 5mg daily", "Losartan 50mg daily", "Metoprolol 25mg BID"],
    "Diabetes": ["Metformin 500mg BID", "Insulin glargine 20 units at bedtime"],
    "Edema": ["Furosemide 40mg daily", "Spironolactone 25mg daily"],
    "Anemia": ["Erythropoietin 4000 units weekly", "Iron supplement 325mg daily"],
    "Bone": ["Calcium carbonate 500mg TID", "Vitamin D3 1000 IU daily"],
}

DIETARY_RESTRICTIONS = [
    "Low sodium (2g/day), fluid restriction (1.5L/day)",
    "Low potassium diet, avoid bananas and oranges",
    "Low protein diet (0.8g/kg/day), low phosphorus",
    "Diabetic diet with carb counting, low sodium",
    "Fluid restriction (1L/day), low sodium (1.5g/day)",
]

WARNING_SIGNS = [
    "Swelling in legs or face, shortness of breath, decreased urine output",
    "Chest pain, severe headache, blood in urine",
    "Confusion, extreme fatigue, nausea and vomiting",
    "Rapid weight gain (>2kg in 2 days), difficulty breathing",
    "High fever, severe back pain, unable to urinate",
]

DISCHARGE_INSTRUCTIONS = [
    "Monitor blood pressure daily, weigh yourself daily, track fluid intake",
    "Take all medications as prescribed, attend all follow-up appointments",
    "Check blood sugar 4 times daily, maintain medication log",
    "Avoid NSAIDs (ibuprofen, aspirin), no contrast dyes without approval",
    "Low-impact exercise 30 min daily, avoid dehydration",
]


def generate_patient_report(patient_id):
    """Generate a single patient discharge report"""
    
    # Generate basic patient info
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"
    
    # Random discharge date within last 3 months
    discharge_date = datetime.now() - timedelta(days=random.randint(1, 90))
    
    # Select diagnosis and related info
    diagnosis = random.choice(DIAGNOSES)
    
    # Build medication list based on diagnosis
    meds = []
    if "CKD" in diagnosis or "Chronic" in diagnosis:
        meds.extend(random.sample(MEDICATIONS["CKD"], random.randint(2, 3)))
        meds.extend(random.sample(MEDICATIONS["HTN"], 1))
        meds.extend(random.sample(MEDICATIONS["Anemia"], 1))
    elif "Diabetic" in diagnosis:
        meds.extend(random.sample(MEDICATIONS["Diabetes"], 2))
        meds.extend(random.sample(MEDICATIONS["CKD"], 1))
    elif "Hypertensive" in diagnosis:
        meds.extend(random.sample(MEDICATIONS["HTN"], 2))
        meds.extend(random.sample(MEDICATIONS["CKD"], 1))
    else:
        meds.extend(random.sample(MEDICATIONS["CKD"], 2))
    
    # Lab values
    lab_values = {
        "creatinine": round(random.uniform(1.5, 4.5), 1),
        "egfr": random.randint(25, 60),
        "potassium": round(random.uniform(3.8, 5.2), 1),
        "hemoglobin": round(random.uniform(9.5, 12.5), 1),
        "albumin": round(random.uniform(3.0, 4.2), 1),
    }
    
    # Follow-up timing
    follow_up_days = random.choice([7, 14, 21, 30])
    follow_up_date = discharge_date + timedelta(days=follow_up_days)
    
    report = {
        "patient_id": f"P{patient_id:04d}",
        "patient_name": full_name,
        "date_of_birth": fake.date_of_birth(minimum_age=35, maximum_age=80).strftime("%Y-%m-%d"),
        "gender": random.choice(["Male", "Female"]),
        "admission_date": (discharge_date - timedelta(days=random.randint(3, 10))).strftime("%Y-%m-%d"),
        "discharge_date": discharge_date.strftime("%Y-%m-%d"),
        "primary_diagnosis": diagnosis,
        "secondary_diagnoses": random.sample(
            ["Hypertension", "Type 2 Diabetes", "Anemia", "Hyperkalemia", "Metabolic Acidosis"],
            random.randint(1, 3)
        ),
        "medications": meds,
        "lab_values": lab_values,
        "dietary_restrictions": random.choice(DIETARY_RESTRICTIONS),
        "follow_up": f"Nephrology clinic on {follow_up_date.strftime('%Y-%m-%d')} ({follow_up_days} days)",
        "warning_signs": random.choice(WARNING_SIGNS),
        "discharge_instructions": random.choice(DISCHARGE_INSTRUCTIONS),
        "attending_physician": f"Dr. {fake.last_name()}",
        "contact_number": fake.phone_number(),
        "emergency_contact": {
            "name": fake.name(),
            "relationship": random.choice(["Spouse", "Son", "Daughter", "Sibling"]),
            "phone": fake.phone_number(),
        }
    }
    
    return report


def generate_all_patients(num_patients=30):
    """Generate multiple patient reports"""
    patients = []
    
    print(f"Generating {num_patients} patient reports...")
    for i in range(1, num_patients + 1):
        patient = generate_patient_report(i)
        patients.append(patient)
        print(f"  Generated: {patient['patient_name']} - {patient['primary_diagnosis']}")
    
    return patients


def save_to_json(patients, filepath="data/patients/patients.json"):
    """Save patient reports to JSON file"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(patients, f, indent=2, ensure_ascii=False)
    
    print(f"\n Saved {len(patients)} patients to {filepath}")


def save_to_sqlite(patients, db_path="data/patients/patients.db"):
    """Save patient reports to SQLite database"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            patient_name TEXT NOT NULL,
            date_of_birth TEXT,
            gender TEXT,
            admission_date TEXT,
            discharge_date TEXT,
            primary_diagnosis TEXT,
            secondary_diagnoses TEXT,
            medications TEXT,
            lab_values TEXT,
            dietary_restrictions TEXT,
            follow_up TEXT,
            warning_signs TEXT,
            discharge_instructions TEXT,
            attending_physician TEXT,
            contact_number TEXT,
            emergency_contact TEXT
        )
    ''')
    
    # Insert patients
    for patient in patients:
        cursor.execute('''
            INSERT OR REPLACE INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient['patient_id'],
            patient['patient_name'],
            patient['date_of_birth'],
            patient['gender'],
            patient['admission_date'],
            patient['discharge_date'],
            patient['primary_diagnosis'],
            json.dumps(patient['secondary_diagnoses']),
            json.dumps(patient['medications']),
            json.dumps(patient['lab_values']),
            patient['dietary_restrictions'],
            patient['follow_up'],
            patient['warning_signs'],
            patient['discharge_instructions'],
            patient['attending_physician'],
            patient['contact_number'],
            json.dumps(patient['emergency_contact'])
        ))
    
    conn.commit()
    conn.close()
    
    print(f" Saved {len(patients)} patients to SQLite: {db_path}")


def print_sample_report(patients, num_samples=2):
    """Print sample patient reports for verification"""
    print("\n" + "="*80)
    print("SAMPLE PATIENT REPORTS")
    print("="*80)
    
    for patient in patients[:num_samples]:
        print(f"\n Patient: {patient['patient_name']} ({patient['patient_id']})")
        print(f"   Diagnosis: {patient['primary_diagnosis']}")
        print(f"   Discharge Date: {patient['discharge_date']}")
        print(f"   Medications: {len(patient['medications'])} prescribed")
        print(f"   Follow-up: {patient['follow_up']}")


if __name__ == "__main__":
    # Generate 30 patients (more than required 25)
    patients = generate_all_patients(num_patients=30)
    
    # Save to both JSON and SQLite
    save_to_json(patients)
    save_to_sqlite(patients)
    
    # Print samples
    print_sample_report(patients)
    
    print("\n" + "="*80)
    print(" PATIENT DATA GENERATION COMPLETE!")
    print("="*80)
    print(f"Total Patients: {len(patients)}")
    print("Files Created:")
    print("  - data/patients/patients.json")
    print("  - data/patients/patients.db")
    print("\nNext Step: Process the nephrology PDF for RAG")
