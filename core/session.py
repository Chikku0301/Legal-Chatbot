"""
Session Manager — Handles persistent user state for the Telegram Bot.

This module stores each user's conversation state and collected data
in a JSON file. It allows the Telegram bot to maintain separate
sessions for multiple users.

A file lock is used to prevent race conditions when multiple users
access or update the session file simultaneously.
"""

import os
import json
from filelock import FileLock


# ============================================================
# DIRECTORY AND FILE CONFIGURATION
# ============================================================

# Get the absolute path of the directory containing this file.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Move one level up to get the project's root directory.
_PROJECT_DIR = os.path.dirname(_THIS_DIR)

# Define the outputs directory where session data will be stored.
OUTPUT_DIR = os.path.join(_PROJECT_DIR, "outputs")

# Create the outputs directory if it does not already exist.
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Path of the JSON file used to store all user sessions.
SESSION_DB_PATH = os.path.join(OUTPUT_DIR, "sessions.json")

# Path of the lock file used to control concurrent access
# to the sessions JSON file.
SESSION_LOCK_PATH = os.path.join(
    OUTPUT_DIR,
    "sessions.json.lock"
)


# ============================================================
# CONVERSATION STATES
# ============================================================

# This class acts like an enum and contains all possible states
# of a user's conversation with the Telegram bot.
#
# The bot checks the user's current state to determine what
# information it should ask for or what action it should perform next.
class State:

    # Initial state when a new user starts interacting with the bot.
    START = "START"

    # The bot is waiting for the user to describe their legal problem.
    ASK_PROBLEM = "ASK_PROBLEM"

    # The bot is asking whether the user wants to generate
    # or provide legal documents.
    ASK_DOCS = "ASK_DOCS"

    # The bot is collecting information required for the
    # selected legal workflow or document.
    COLLECT_INFO = "COLLECT_INFO"

    # The user has requested help or an explanation for
    # a legal field or question.
    WAITING_HELP = "WAITING_HELP"

    # The bot is asking whether the user wants to track
    # a legal case.
    ASK_TRACKER = "ASK_TRACKER"

    # The bot is waiting for a case submission or
    # evidence deadline.
    ASK_DEADLINE = "ASK_DEADLINE"

    # The bot is waiting for the user to provide
    # a court hearing date.
    ASK_HEARING = "ASK_HEARING"

    # The current legal assistance workflow has been completed.
    DONE = "DONE"


# ============================================================
# SESSION FILE OPERATIONS
# ============================================================

def _load_sessions() -> dict:
    """
    Load all user sessions from the JSON file.

    Returns:
        dict: A dictionary containing session data for all users.

    If the session file does not exist or contains invalid JSON,
    an empty dictionary is returned.
    """

    # Check whether the sessions file already exists.
    if os.path.exists(SESSION_DB_PATH):
        try:
            # Open and read the JSON file.
            with open(SESSION_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        # If the JSON file is corrupted or invalid,
        # return an empty dictionary instead of crashing.
        except json.JSONDecodeError:
            return {}

    # Return an empty dictionary if no session file exists yet.
    return {}


def _save_sessions(data: dict):
    """
    Save all user session data to the JSON file.

    Args:
        data (dict): Dictionary containing all user sessions.
    """

    # Open the JSON file in write mode and store the session data.
    # indent=2 makes the JSON file easier for humans to read.
    with open(SESSION_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ============================================================
# GET USER SESSION
# ============================================================

def get_user_session(user_id: int) -> dict:
    """
    Retrieve the session data of a specific user.

    If the user does not already have a session, a default session
    is returned with the conversation state set to START.

    Args:
        user_id (int): Unique Telegram user ID.

    Returns:
        dict: The user's current session state and collected data.
    """

    # Convert the Telegram user ID to a string because JSON keys
    # are stored as strings.
    user_id_str = str(user_id)

    # Acquire the file lock before reading the session file.
    # This prevents simultaneous access from causing conflicts.
    with FileLock(SESSION_LOCK_PATH):

        # Load all existing user sessions.
        sessions = _load_sessions()

        # If the user has no existing session, return
        # a default session without saving it yet.
        if user_id_str not in sessions:
            return {
                "state": State.START,
                "data": {}
            }

        # Return the existing session data for the user.
        return sessions[user_id_str]


# ============================================================
# UPDATE USER SESSION
# ============================================================

def update_user_session(
    user_id: int,
    new_state: str = None,
    updates: dict = None
):
    """
    Create or update a user's session.

    The function can update:
        - The user's current conversation state
        - The collected data dictionary
        - Both at the same time

    Args:
        user_id (int): Unique Telegram user ID.
        new_state (str, optional): New conversation state.
        updates (dict, optional): New data to merge into
            the user's existing session data.
    """

    # Convert the user ID to a string for JSON storage.
    user_id_str = str(user_id)

    # Acquire the file lock before modifying the JSON file.
    # This prevents race conditions when multiple Telegram users
    # interact with the bot at the same time.
    with FileLock(SESSION_LOCK_PATH):

        # Load all existing sessions.
        sessions = _load_sessions()

        # --------------------------------------------------------
        # Initialize a new session if the user does not exist.
        # --------------------------------------------------------
        if user_id_str not in sessions:
            sessions[user_id_str] = {
                "state": State.START,
                "data": {}
            }

        # --------------------------------------------------------
        # Update the conversation state if a new state is provided.
        # --------------------------------------------------------
        if new_state is not None:
            sessions[user_id_str]["state"] = new_state

        # --------------------------------------------------------
        # Update the user's collected information.
        #
        # .update() merges the new dictionary with existing data.
        #
        # Example:
        # Existing:
        # {"name": "John"}
        #
        # New update:
        # {"city": "Chennai"}
        #
        # Result:
        # {"name": "John", "city": "Chennai"}
        # --------------------------------------------------------
        if updates is not None:
            sessions[user_id_str]["data"].update(updates)

        # Save the updated sessions back to the JSON file.
        _save_sessions(sessions)


# ============================================================
# CLEAR USER SESSION
# ============================================================

def clear_user_session(user_id: int):
    """
    Delete a user's session data.

    This can be used when:
        - The user starts a completely new conversation
        - The legal workflow is completed
        - The bot needs to reset the user's conversation state

    Args:
        user_id (int): Unique Telegram user ID.
    """

    # Convert the user ID to a string for JSON lookup.
    user_id_str = str(user_id)

    # Acquire the file lock before modifying the session file.
    with FileLock(SESSION_LOCK_PATH):

        # Load all existing sessions.
        sessions = _load_sessions()

        # Check whether the user currently has a stored session.
        if user_id_str in sessions:

            # Remove the user's session from the dictionary.
            del sessions[user_id_str]

            # Save the updated dictionary back to the JSON file.
            _save_sessions(sessions)