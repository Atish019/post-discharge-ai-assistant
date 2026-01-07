import sqlite3
import json
from pathlib import Path
from src.utils.logger import log_system

DB_PATH = "data/patients/patients.db"
JSON_PATH = "data/patients/patients.json"

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            discharge_date TEXT,
            primary_diagnosis TEXT,
            medications TEXT,
            dietary_restrictions TEXT,
            follow_up TEXT,
            warning_signs TEXT,
            discharge_instructions TEXT
        )
    """)

    with open(JSON_PATH) as f:
        patients = json.load(f)

    cursor.execute("DELETE FROM patients")

    for p in patients:
        cursor.execute("""
            INSERT INTO patients (
                patient_name, discharge_date, primary_diagnosis,
                medications, dietary_restrictions, follow_up,
                warning_signs, discharge_instructions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["patient_name"],
            p["discharge_date"],
            p["primary_diagnosis"],
            ", ".join(p["medications"]),
            p["dietary_restrictions"],
            p["follow_up"],
            p["warning_signs"],
            p["discharge_instructions"]
        ))

    conn.commit()
    conn.close()
    log_system(" SQLite patient database initialized")

if __name__ == "__main__":
    setup_database()
