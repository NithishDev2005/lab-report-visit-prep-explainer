import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "visit_prep.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS report_sessions (
        session_id TEXT PRIMARY KEY,
        patient_name TEXT,
        collection_date TEXT,
        consent_given INTEGER DEFAULT 0,
        status TEXT,
        created_at TEXT
    )''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS extracted_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        test_key TEXT,
        test_name TEXT,
        result_value REAL,
        result_str TEXT,
        unit TEXT,
        printed_range TEXT,
        lab_flag TEXT,
        ocr_confidence REAL,
        is_ambiguous INTEGER DEFAULT 0
    )''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS visit_prep_notes (
        note_id TEXT PRIMARY KEY,
        session_id TEXT,
        summary_markdown TEXT,
        doctor_questions_json TEXT,
        critical_alerts_json TEXT,
        approval_status TEXT,
        approved_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()
