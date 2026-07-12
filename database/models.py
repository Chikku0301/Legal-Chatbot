"""
Database Models — SQL table schemas for LegalBot (MySQL).
"""

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    phone_number VARCHAR(20) PRIMARY KEY,
    name         VARCHAR(200),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    phone_number      VARCHAR(20) PRIMARY KEY,
    current_step      INTEGER DEFAULT 1,
    workflow          VARCHAR(200),
    last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CASE_INPUTS_TABLE = """
CREATE TABLE IF NOT EXISTS case_inputs (
    id           INTEGER AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    field_name   VARCHAR(100) NOT NULL,
    field_value  TEXT
);
"""

CASES_TABLE = """
CREATE TABLE IF NOT EXISTS cases (
    case_id      VARCHAR(20) PRIMARY KEY,
    phone_number VARCHAR(20),
    category     VARCHAR(200),
    court        VARCHAR(200),
    filing_date  DATE,
    hearing_date DATE,
    pdf_path     TEXT,
    status       VARCHAR(50) DEFAULT 'Filed'
);
"""

ALL_TABLES = [USERS_TABLE, SESSIONS_TABLE, CASE_INPUTS_TABLE, CASES_TABLE]
