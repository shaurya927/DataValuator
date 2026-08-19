import sqlite3
db_path = r'd:\Users\imsha\Documents\Projects\DataValuator\backend\data\db\dataValuator.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM experiments ORDER BY started_at DESC LIMIT 1")
print(dict(cursor.fetchone()))
import os
if os.path.exists('backend/experiment_error.txt'):
    with open('backend/experiment_error.txt', 'r') as f:
        print(f.read())
elif os.path.exists('experiment_error.txt'):
    with open('experiment_error.txt', 'r') as f:
        print(f.read())
conn.commit()
