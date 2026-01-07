"""
Initialize the SQLite database with the schema defined in schema.sql.

If the database or tables already exist, they will not be recreated.
"""

import sqlite3
from pathlib import Path
import traceback

DB_PATH = Path("trading.db")
SCHEMA_PATH = Path("schema.sql")

try:
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.close()
except Exception as e:
    print(f"Error initializing database: {e}")
    traceback.print_exc()
