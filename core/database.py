"""
SQLite Database Connection and Schema Management.
"""

import os
import sqlite3
import json

# Same outputs directory as session manager
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_THIS_DIR)
OUTPUT_DIR = os.path.join(_PROJECT_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DB_PATH = os.path.join(OUTPUT_DIR, "legal_bot_cases.db")


def get_connection() -> sqlite3.Connection:
    """Returns a connected SQLite Connection object with row factory set."""
    # check_same_thread=False allows background threads to use connection
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Cases Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            dispute_category TEXT NOT NULL,
            procedure_name TEXT NOT NULL,
            court_name TEXT NOT NULL,
            case_status TEXT NOT NULL,
            form_responses TEXT NOT NULL,
            filing_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 3. Case Deadlines (Reminders) Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_label TEXT NOT NULL,
            due_date DATE NOT NULL,
            reminder_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    ''')

    conn.commit()
    conn.close()

# Always initialize schema on load
init_db()
