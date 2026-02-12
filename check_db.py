import sqlite3
import os

db_path = "data/keiba.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

query = """
SELECT e.passing_order, h.name, r.name, r.date
FROM race_entries e 
JOIN horses h ON e.horse_id = h.id 
JOIN races r ON e.race_id = r.id
WHERE h.name LIKE '%ドウデュース%'
ORDER BY r.date DESC;
"""

cursor.execute(query)
results = cursor.fetchall()

if not results:
    print("No entries found for ドウデュース")
else:
    for row in results:
        print(f"Horse: {row[1]}, Race: {row[2]}, Date: {row[3]}, Passing Order: {row[0]}")

conn.close()
