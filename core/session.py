"""
Session Manager — Handles persistent user state for the Telegram Bot.
Stores user conversation state in a JSON file to support asynchronous, concurrent routing.
"""

import os
import json
from filelock import FileLock

# We'll use the same outputs directory as the case tracker
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_THIS_DIR)
OUTPUT_DIR = os.path.join(_PROJECT_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SESSION_DB_PATH = os.path.join(OUTPUT_DIR, "sessions.json")
SESSION_LOCK_PATH = os.path.join(OUTPUT_DIR, "sessions.json.lock")

# Define our states
class State:
    START = "START"
    ASK_PROBLEM = "ASK_PROBLEM"
    ASK_DOCS = "ASK_DOCS"
    COLLECT_INFO = "COLLECT_INFO"
    WAITING_HELP = "WAITING_HELP"
    ASK_TRACKER = "ASK_TRACKER"
    ASK_DEADLINE = "ASK_DEADLINE"
    ASK_HEARING = "ASK_HEARING"
    DONE = "DONE"


def _load_sessions() -> dict:
    if os.path.exists(SESSION_DB_PATH):
        try:
            with open(SESSION_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def _save_sessions(data: dict):
    with open(SESSION_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_session(user_id: int) -> dict:
    """Retrieve a user's session data. Returns a default dictionary if none exists."""
    user_id_str = str(user_id)
    with FileLock(SESSION_LOCK_PATH):
        sessions = _load_sessions()
        if user_id_str not in sessions:
            return {"state": State.START, "data": {}}
        return sessions[user_id_str]


def update_user_session(user_id: int, new_state: str = None, updates: dict = None):
    """Update a user's session state and/or data dictionary."""
    user_id_str = str(user_id)
    with FileLock(SESSION_LOCK_PATH):
        sessions = _load_sessions()
        
        # Initialize if missing
        if user_id_str not in sessions:
            sessions[user_id_str] = {"state": State.START, "data": {}}
            
        if new_state is not None:
            sessions[user_id_str]["state"] = new_state
            
        if updates is not None:
            sessions[user_id_str]["data"].update(updates)
            
        _save_sessions(sessions)


def clear_user_session(user_id: int):
    """Delete a user's session data (e.g. on /start or completion)."""
    user_id_str = str(user_id)
    with FileLock(SESSION_LOCK_PATH):
        sessions = _load_sessions()
        if user_id_str in sessions:
            del sessions[user_id_str]
            _save_sessions(sessions)
