"""
Database Connection — MySQL connection helper and table initialisation.
"""

import os
import mysql.connector

from database.models import ALL_TABLES


# ─── Connection ───────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "legalbot"),
}


def get_connection():
    """Return a new mysql.connector connection using the configured DB_CONFIG."""
    return mysql.connector.connect(**DB_CONFIG)


# ─── Table Initialisation ────────────────────────────────────────────────────
def init_db():
    """Create all required tables if they do not already exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        for table_sql in ALL_TABLES:
            cur.execute(table_sql)
        conn.commit()
        cur.close()
    finally:
        conn.close()
