"""
Case Tracker — MySQL database case creation, reminders, display.
"""

import os
import datetime
from utils.ui import C, header
from database.db import get_connection

# ─── Paths ────────────────────────────────────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_THIS_DIR)
OUTPUT_DIR = os.path.join(_PROJECT_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _next_case_id() -> str:
    """Generate a sequential case ID like SC-1001, SC-1002, ..."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cases")
        count = cur.fetchone()[0]
        cur.close()
        return f"SC-{1000 + count + 1}"
    finally:
        conn.close()


def create_case(case_data: dict, workflow: dict, court: str, deadline_date: str = None, deadline_label: str = None, hearing_date: str = None) -> str:
    """Inserts a new case into the MySQL database."""
    conn = get_connection()
    try:
        case_id = _next_case_id()
        phone = case_data.get("phone", "N/A")
        category = workflow.get("title", "Legal Dispute")
        filing_date = datetime.date.today().strftime("%Y-%m-%d")
        
        try:
            h_date = datetime.datetime.strptime(hearing_date, "%d %b %Y").strftime("%Y-%m-%d")
        except:
            h_date = None

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cases (case_id, phone_number, category, court, filing_date, hearing_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (case_id, phone, category, court, filing_date, h_date, "Filed")
        )
        conn.commit()
        cur.close()
        return case_id
    finally:
        conn.close()


def check_reminders():
    """Returns a list of reminders due within 7 days that haven't been sent."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        today = datetime.date.today()
        target = today + datetime.timedelta(days=7)
        
        cur.execute(
            """
            SELECT case_id, hearing_date FROM cases 
            WHERE hearing_date IS NOT NULL 
            AND hearing_date <= %s AND hearing_date >= %s
            """,
            (target.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
        )
        rows = cur.fetchall()
        cur.close()
        
        reminders = []
        for row in rows:
            case_id, h_date = row[0], row[1]
            days_left = (h_date - today).days
            case_summary = {
                "case_id": case_id,
                "deadline_label": "Hearing",
                "hearing_date": h_date.strftime("%Y-%m-%d"),
                "next_deadline": h_date.strftime("%Y-%m-%d")
            }
            reminders.append((case_summary, days_left))
        return reminders
    except:
        return []
    finally:
        conn.close()


def display_case_tracker(case_id: str):
    """Display case information from the database."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT case_id, phone_number, category, court,
                   filing_date, hearing_date, pdf_path, status
            FROM cases WHERE case_id = %s
            """,
            (case_id,),
        )
        row = cur.fetchone()
        cur.close()

        if row:
            header(f"📋 CASE TRACKER — {case_id}")
            print(f"  {'Case ID':<22}: {C.BOLD}{row[0]}{C.RESET}")
            print(f"  {'Case Type':<22}: {row[2]}")
            print(f"  {'Court':<22}: {row[3]}")
            print(f"  {'Status':<22}: {C.GREEN}{row[7]}{C.RESET}")
            print(f"  {'Filing Date':<22}: {row[4]}")
            print(f"  {'Hearing Date':<22}: {C.YELLOW}{row[5]}{C.RESET}")
            print()
            return
    finally:
        conn.close()
    print(f"  {C.RED}Case {case_id} not found.{C.RESET}")


def get_case_tracker_text(case_id: str) -> str:
    """Return case tracker info as a plain-text string (for Telegram)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT case_id, phone_number, category, court,
                   filing_date, hearing_date, pdf_path, status
            FROM cases WHERE case_id = %s
            """,
            (case_id,),
        )
        row = cur.fetchone()
        cur.close()

        if row:
            return (
                f"📋 CASE TRACKER — {case_id}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 Case ID:       {row[0]}\n"
                f"📂 Case Type:     {row[2]}\n"
                f"🏛 Court:         {row[3]}\n"
                f"✅ Status:        {row[7]}\n"
                f"📅 Filing Date:   {row[4]}\n"
                f"📆 Hearing Date:  {row[5]}"
            )
    finally:
        conn.close()
    return f"❌ Case {case_id} not found."
