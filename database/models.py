"""
Database Models — SQL table schemas for LegalBot (MySQL).

This file contains the SQL CREATE TABLE statements required
to initialize the application's database.
"""


# ============================================================
# USERS TABLE
# ============================================================
# Stores basic information about each user interacting with
# the LegalBot.
#
# The phone number is used as the unique identifier for a user.
# ============================================================

USERS_TABLE = """

CREATE TABLE IF NOT EXISTS users (

    # Unique identifier for each user
    phone_number VARCHAR(20) PRIMARY KEY,

    # Name provided by the user
    name VARCHAR(200),

    # Timestamp when the user was first registered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

"""


# ============================================================
# SESSIONS TABLE
# ============================================================
# Stores the current conversation/session state of a user.
#
# This allows the chatbot to remember where the user left off
# in the legal workflow and continue the conversation later.
# ============================================================

SESSIONS_TABLE = """

CREATE TABLE IF NOT EXISTS sessions (

    # Phone number of the user.
    # Used as the primary key because each user has one active session.
    phone_number VARCHAR(20) PRIMARY KEY,

    # Represents the current step in the chatbot workflow.
    # Default value is 1 when a new session is created.
    current_step INTEGER DEFAULT 1,

    # Stores the selected legal workflow or dispute category.
    # Example: "Consumer Complaint", "Property Dispute"
    workflow VARCHAR(200),

    # Stores the timestamp of the user's most recent interaction.
    last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

"""


# ============================================================
# CASE INPUTS TABLE
# ============================================================
# Stores individual pieces of information collected from users
# while filling out a legal workflow.
#
# Each case field is stored as a separate row.
#
# Example:
# field_name  -> "complainant_name"
# field_value -> "John Doe"
# ============================================================

CASE_INPUTS_TABLE = """

CREATE TABLE IF NOT EXISTS case_inputs (

    # Unique ID for each input field entry.
    # AUTO_INCREMENT automatically generates the ID.
    id INTEGER AUTO_INCREMENT PRIMARY KEY,

    # Identifies which user provided this information.
    phone_number VARCHAR(20) NOT NULL,

    # Name of the legal form field.
    # Example: "respondent_name", "incident_date"
    field_name VARCHAR(100) NOT NULL,

    # Value entered by the user for the corresponding field.
    # TEXT is used because some fields may contain long descriptions.
    field_value TEXT

);

"""


# ============================================================
# CASES TABLE
# ============================================================
# Stores information about legal cases created by users.
#
# This table is mainly used for case tracking, including
# important dates, generated documents, and case status.
# ============================================================

CASES_TABLE = """

CREATE TABLE IF NOT EXISTS cases (

    # Unique identifier assigned to each legal case.
    case_id VARCHAR(20) PRIMARY KEY,

    # Phone number of the user who created the case.
    phone_number VARCHAR(20),

    # Type or category of the legal dispute.
    # Example: "Consumer Dispute", "Property Dispute"
    category VARCHAR(200),

    # Court or authority where the case should be filed.
    court VARCHAR(200),

    # Date on which the case was officially filed.
    filing_date DATE,

    # Deadline or date for submitting required documents/evidence.
    submission_date DATE,

    # Scheduled date for the court hearing.
    hearing_date DATE,

    # File path of the generated PDF document.
    pdf_path TEXT,

    # Current status of the case.
    # Default status is "Filed".
    status VARCHAR(50) DEFAULT 'Filed'

);

"""


# ============================================================
# ALL TABLES
# ============================================================
# A list containing all SQL table creation queries.
#
# This can be used during database initialization to create
# all required tables by iterating through this list.
# ============================================================

ALL_TABLES = [
    USERS_TABLE,
    SESSIONS_TABLE,
    CASE_INPUTS_TABLE,
    CASES_TABLE
]