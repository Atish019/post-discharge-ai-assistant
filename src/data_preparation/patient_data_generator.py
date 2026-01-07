"""
Patient Data Generator
Generates 25+ realistic dummy post-discharge patient reports for nephrology cases
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Patient names
PATIENT_NAMES = [
    "John Smith", "Emily Brown", "Michael Johnson", "Sarah Wilson",
    "David Miller", "Sophia Taylor", "Daniel Anderson", "Olivia Thomas",
    "James Jackson", "Emma White", "Robert Harris", "Ava Martin",
    "William Thompson", "Isabella Garcia", "Joseph Martinez",
    "Mia Robinson", "Charles Clark", "Amelia Rodriguez",
    "Thomas Lewis", "Charlotte Lee", "Christopher Walker",
    "Harper Hall", "Anthony Allen", "Evelyn Young", "Andrew King",
    "Matthew Scott", "Abigail Green", "Ryan Adams", "Elizabeth Baker",
    "Joshua Nelson", "Sofia Carter"
]

# Nephrology diagnoses
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

# Medications by category
MEDICATIONS = {
    "CKD": [
        "Lisinopril 10mg daily",
        "Furosemide 20mg twice daily",
        "Sodium bicarbonate 650mg TID"
    ],
    "HTN": [
        "Amlodipine 5mg daily",
        "Losartan 50mg daily",
        "Metoprolol 25mg BID"
    ],
    "Diabetes": [
        "Metformin 500mg BID",
        "Insulin glargine 20 units at bedtime"
    ],
    "Edema": [
        "Furosemide 40mg daily",
        "Spironolactone 25mg daily"
    ],
    "Anemia": [
        "Erythropoietin 4000 units weekly",
        "Iron supplement 325mg daily"
    ],
    "Bone": [
        "Calcium carbonate 500mg TID",
        "Vitamin D3 1000 IU daily"
    ]
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

DOCTOR_NAMES = [
    "Dr. Anderson", "Dr. Martinez", "Dr. Thompson", "Dr. Williams",
    "Dr. Johnson", "Dr. Brown", "Dr. Davis", "Dr. Wilson"
]

EMERGENCY_CONTACTS = [
    ("Mary Smith", "Spouse"), ("John Brown Jr.", "Son"),
    ("Lisa Johnson", "Daughter"), ("Robert Wilson", "Brother"),
    ("Susan Miller", "Sister"), ("David Taylor", "Son"),
    ("Jennifer Anderson", "Daughter"), ("Michael Thomas", "Spouse")
]


def generate_phone():
    """Generate fake US phone number"""
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"


def generate_patient_report(patient_id, patient_name):
    """Generate a single patient discharge report"""
    
    # Random discharge date within last 3 months
    discharge_date = datetime.now() - timedelta(days=random.randint(1, 90))
    admission_date = discharge_date - timedelta(days=random.randint(3, 10))
    
    # Select diagnosis
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
    
    # Follow-up
    follow_up_days = random.choice([7, 14, 21, 30])
    follow_up_date = discharge_date + timedelta(days=follow_up_days)
    
    # Emergency contact
    ec_name, ec_relation = random.choice(EMERGENCY_CONTACTS)
    
    # Generate DOB (35-80 years old)
    age_days = random.randint(35*365, 80*365)
    dob = datetime.now() - timedelta(days=age_days)
    
    report = {
        "patient_id": f"P{patient_id:04d}",
        "patient_name": patient_name,
        "date_of_birth": dob.strftime("%Y-%m-%d"),
        "gender": random.choice(["Male", "Female"]),
        "admission_date": admission_date.strftime("%Y-%m-%d"),
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
        "attending_physician": random.choice(DOCTOR_NAMES),
        "contact_number": generate_phone(),
        "emergency_contact": {
            "name": ec_name,
            "relationship": ec_relation,
            "phone": generate_phone()
        }
    }
    
    return report


def generate_all_patients():
    """Generate all patient reports"""
    patients = []
    
    print(f" Generating {len(PATIENT_NAMES)} patient reports...\n")
    
    for i, name in enumerate(PATIENT_NAMES, start=1):
        patient = generate_patient_report(i, name)
        patients.append(patient)
        print(f"   {i:2d}. {patient['patient_name']:25s} - {patient['primary_diagnosis']}")
    
    return patients


def save_to_json(patients, filepath="data/patients/patients.json"):
    """Save patient reports to JSON file"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(patients, f, indent=2, ensure_ascii=False)
    
    print(f"\n Saved {len(patients)} patients to {filepath}")


def print_sample_report(patients, num_samples=2):
    """Print sample patient reports"""
    print("\n" + "="*80)
    print(" SAMPLE PATIENT REPORTS")
    print("="*80)
    
    for patient in patients[:num_samples]:
        print(f"\n Patient: {patient['patient_name']} ({patient['patient_id']})")
        print(f"    Diagnosis: {patient['primary_diagnosis']}")
        print(f"    Discharge: {patient['discharge_date']}")
        print(f"    Medications: {len(patient['medications'])} prescribed")
        print(f"    Follow-up: {patient['follow_up']}")
        print(f"    Creatinine: {patient['lab_values']['creatinine']} mg/dL")


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" POST-DISCHARGE PATIENT DATA GENERATOR")
    print("="*80 + "\n")
    
    # Generate patients
    patients = generate_all_patients()
    
    # Save to JSON
    save_to_json(patients)
    
    # Print samples
    print_sample_report(patients)
    