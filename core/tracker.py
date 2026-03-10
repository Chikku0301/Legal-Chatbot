"""
Case Tracker — SQLite database case creation, reminders, display.
"""

import json
import datetime

from utils.ui import C, header
from core.database import get_connection


def _get_or_create_user(conn, case_data: dict) -> int:
    """Gets existing user ID or creates a new user based on telegram_id or phone."""
    cursor = conn.cursor()
    
    # Try using telegram_id if it exists, otherwise phone
    telegram_id = case_data.get("telegram_id")
    phone = case_data.get("phone", "N/A")
    name = case_data.get("user_name", "Unknown")

    if telegram_id:
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        
        cursor.execute(
            "INSERT INTO users (telegram_id, full_name, phone_number) VALUES (?, ?, ?)",
            (telegram_id, name, phone)
        )
        return cursor.lastrowid
    
    # Fallback if no telegram_id was passed
    cursor.execute("SELECT id FROM users WHERE phone_number = ?", (phone,))
    row = cursor.fetchone()
    if row and phone != "N/A":
        return row["id"]
        
    # Generate a dummy telegram ID for CLI users if needed
    dummy_id = f"cli_{datetime.datetime.now().timestamp()}"
    cursor.execute(
        "INSERT INTO users (telegram_id, full_name, phone_number) VALUES (?, ?, ?)",
        (dummy_id, name, phone)
    )
    return cursor.lastrowid


def create_case(case_data: dict, workflow: dict, court: str) -> str:
    """Inserts a new case and its deadlines into the SQLite database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get User
        user_id = _get_or_create_user(conn, case_data)

        # Generate Case Number
        cursor.execute("SELECT COUNT(*) as count FROM cases")
        count = cursor.fetchone()["count"]
        case_number = f"SC-{1000 + count + 1}"

        filing_date = datetime.date.today()

        # Insert Case
        form_responses_json = json.dumps(case_data)
        
        cursor.execute('''
            INSERT INTO cases (
                case_number, user_id, dispute_category, procedure_name, 
                court_name, case_status, form_responses, filing_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_number, user_id, workflow["title"], workflow["title"], 
            court, "Filed", form_responses_json, filing_date
        ))
        
        case_id = cursor.lastrowid

        # Insert User-Provided Deadlines (they are strings e.g. "20 Oct")
        # Since they are strings, we will store them in due_date. 
        # (SQLite allows storing strings in DATE columns).
        # However, for check_reminders to work, SQLite expects YYYY-MM-DD.
        # Since the user input is free-form ("In 2 weeks"), we will store it directly 
        # and let check_reminders handle "dynamic dates" gently.
        
        user_deadline = case_data.get("user_evidence_deadline", "Unknown")
        user_hearing = case_data.get("user_hearing_date", "Unknown")

        cursor.execute('''
            INSERT INTO case_deadlines (case_id, event_type, event_label, due_date)
            VALUES (?, ?, ?, ?)
        ''', (case_id, "DEADLINE", "Evidence Submission", user_deadline))

        cursor.execute('''
            INSERT INTO case_deadlines (case_id, event_type, event_label, due_date)
            VALUES (?, ?, ?, ?)
        ''', (case_id, "HEARING", "First Hearing", user_hearing))

        conn.commit()
        return case_number
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def check_reminders():
    """Returns a list of reminders due within 7 days that haven't been sent."""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    target_date = today + datetime.timedelta(days=7)
    
    cursor.execute('''
        SELECT cd.id, cd.event_label, cd.due_date, c.case_number 
        FROM case_deadlines cd
        JOIN cases c ON cd.case_id = c.id
        WHERE cd.reminder_sent = 0 
        AND cd.due_date <= ?
        AND cd.due_date >= ?
    ''', (target_date, today))
    
    rows = cursor.fetchall()
    
    reminders = []
    for row in rows:
        due_date = datetime.date.fromisoformat(row["due_date"])
        days_left = (due_date - today).days
        
        # Format it exactly like the old JSON version for compatibility
        case_summary = {
            "case_id": row["case_number"],
            "deadline_label": row["event_label"],
            "next_deadline": row["due_date"]
        }
        reminders.append((case_summary, days_left))
        
    conn.close()
    return reminders


def display_case_tracker(case_number: str):
    """CLI Display for Case Tracker."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, u.full_name 
        FROM cases c
        JOIN users u ON c.user_id = u.id
        WHERE c.case_number = ?
    ''', (case_number,))
    
    case = cursor.fetchone()
    if not case:
        print(f"  {C.RED}Case {case_number} not found.{C.RESET}")
        conn.close()
        return
        
    # Get the next upcoming deadline
    cursor.execute('''
        SELECT * FROM case_deadlines 
        WHERE case_id = ? AND due_date >= DATE('now')
        ORDER BY due_date ASC LIMIT 1
    ''', (case["id"],))
    upcoming = cursor.fetchone()

    header(f"📋 CASE TRACKER — {case_number}")
    print(f"  {'Case ID':<22}: {C.BOLD}{case['case_number']}{C.RESET}")
    print(f"  {'Complainant':<22}: {case['full_name']}")
    print(f"  {'Case Type':<22}: {case['dispute_category']}")
    print(f"  {'Court':<22}: {case['court_name']}")
    print(f"  {'Status':<22}: {C.GREEN}{case['case_status']}{C.RESET}")
    print(f"  {'Filing Date':<22}: {case['filing_date']}")
    
    if upcoming:
        print(f"  {'Next Deadline':<22}: {C.YELLOW}{upcoming['due_date']}{C.RESET}  ({upcoming['event_label']})")
    
    print()
    conn.close()


def get_case_tracker_text(case_number: str) -> str:
    """Return case tracker info as a plain-text string (for Telegram)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, u.full_name 
        FROM cases c
        JOIN users u ON c.user_id = u.id
        WHERE c.case_number = ?
    ''', (case_number,))
    
    case = cursor.fetchone()
    if not case:
        conn.close()
        return f"❌ Case {case_number} not found."
        
    # Get the next upcoming deadline
    cursor.execute('''
        SELECT * FROM case_deadlines 
        WHERE case_id = ? AND due_date >= DATE('now')
        ORDER BY due_date ASC LIMIT 2
    ''', (case["id"],))
    deadlines = cursor.fetchall()
    conn.close()
    
    text = (
        f"📋 CASE TRACKER — {case_number}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Case ID:       {case['case_number']}\n"
        f"👤 Complainant:   {case['full_name']}\n"
        f"📂 Case Type:     {case['dispute_category']}\n"
        f"🏛 Court:         {case['court_name']}\n"
        f"✅ Status:        {case['case_status']}\n"
        f"📅 Filing Date:   {case['filing_date']}\n"
    )
    
    for dl in deadlines:
        text += f"⏰ {dl['event_label']}: {dl['due_date']}\n"
        
    return text