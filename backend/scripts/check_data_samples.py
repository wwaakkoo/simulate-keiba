
import sqlite3
import os
from pathlib import Path

# Connect to database
base_dir = Path(__file__).resolve().parent.parent.parent
db_path = base_dir / "data" / "keiba.db"

print(f"Connecting to database at {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check passing_order samples
    print("\n=== passing_order samples ===")
    cursor.execute("SELECT passing_order FROM race_entries WHERE passing_order IS NOT NULL LIMIT 20")
    for row in cursor.fetchall():
        print(f"'{row[0]}'")

    # Check finish_time samples
    print("\n=== finish_time samples ===")
    cursor.execute("SELECT finish_time FROM race_entries WHERE finish_time IS NOT NULL LIMIT 20")
    for row in cursor.fetchall():
        print(f"'{row[0]}'")

    # Check for potential edge cases (nulls, empty strings)
    cursor.execute("SELECT COUNT(*) FROM race_entries WHERE passing_order IS NULL")
    null_passing = cursor.fetchone()[0]
    print(f"\nNULL passing_order count: {null_passing}")

    cursor.execute("SELECT COUNT(*) FROM race_entries WHERE finish_time IS NULL")
    null_finish = cursor.fetchone()[0]
    print(f"NULL finish_time count: {null_finish}")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
