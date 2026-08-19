import sqlite3
db_path = r'd:\Users\imsha\Documents\Projects\DataValuator\backend\data\db\dataValuator.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM experiments ORDER BY started_at DESC LIMIT 2")
for row in cursor.fetchall():
    print(dict(row))
