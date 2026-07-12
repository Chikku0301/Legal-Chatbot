"""
Session Manager — persistent conversation state via MySQL.
"""

import datetime
from database.db import get_connection


# ─── User Registration ───────────────────────────────────────────────────────

def register_user(phone_number: str, name: str):
    """Insert a user if they don't already exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (phone_number, name, created_at)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name)
            """,
            (phone_number, name, datetime.datetime.now()),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


# ─── Session CRUD ─────────────────────────────────────────────────────────────

def create_session(phone_number: str):
    """Create a new session with current_step=1 and workflow=NULL."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sessions (phone_number, current_step, workflow, last_message_time)
            VALUES (%s, 1, NULL, %s)
            ON DUPLICATE KEY UPDATE
                current_step = 1, workflow = NULL, last_message_time = VALUES(last_message_time)
            """,
            (phone_number, datetime.datetime.now()),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def get_session(phone_number: str) -> dict | None:
    """Return session dict with current_step and workflow, or None."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT current_step, workflow FROM sessions WHERE phone_number = %s",
            (phone_number,),
        )
        row = cur.fetchone()
        cur.close()
        if row:
            return {"current_step": row[0], "workflow": row[1]}
        return None
    finally:
        conn.close()


def update_step(phone_number: str, step: int):
    """Update the user's current workflow step."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sessions
            SET current_step = %s, last_message_time = %s
            WHERE phone_number = %s
            """,
            (step, datetime.datetime.now(), phone_number),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def set_workflow(phone_number: str, workflow: str):
    """Store the classified workflow name in the session."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE sessions SET workflow = %s WHERE phone_number = %s",
            (workflow, phone_number),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


# ─── Case Inputs ──────────────────────────────────────────────────────────────

def save_input(phone_number: str, field_name: str, value: str):
    """Store one user response in case_inputs."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO case_inputs (phone_number, field_name, field_value)
            VALUES (%s, %s, %s)
            """,
            (phone_number, field_name, value),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def get_inputs(phone_number: str) -> dict:
    """Return all stored inputs for the user as {field_name: field_value}."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT field_name, field_value FROM case_inputs WHERE phone_number = %s",
            (phone_number,),
        )
        rows = cur.fetchall()
        cur.close()
        return {row[0]: row[1] for row in rows}
    finally:
        conn.close()


# ─── Cleanup ──────────────────────────────────────────────────────────────────

def clear_session(phone_number: str):
    """Delete the session and all case_inputs for the user."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM case_inputs WHERE phone_number = %s", (phone_number,))
        cur.execute("DELETE FROM sessions WHERE phone_number = %s", (phone_number,))
        conn.commit()
        cur.close()
    finally:
        conn.close()
