import sqlite3
import os

db_paths = [
    r'd:\Users\imsha\Documents\Projects\DataValuator\backend\data\db\dataValuator.db',
    r'd:\Users\imsha\Documents\Projects\DataValuator\backend\DataValuator.db',
    r'd:\Users\imsha\Documents\Projects\DataValuator\backend\sqlite.db'
]

for db_path in db_paths:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE datasets SET type='image_csv' WHERE type='csv' AND (name LIKE '%fashion%' OR name LIKE '%mnist%')")
            conn.commit()
            print(f"Updated {cursor.rowcount} rows in {db_path}.")
        except Exception as e:
            print(f"Error updating {db_path}: {e}")
        finally:
            conn.close()
