import sqlite3
import os

db_paths = [
    r'd:\Users\imsha\Documents\Projects\DataValuator\backend\DataValuator.db',
    r'd:\Users\imsha\Documents\Projects\DataValuator\backend\sqlite.db',
    r'd:\Users\imsha\Documents\Projects\DataValuator\data\db\dataValuator.db',
    r'd:\Users\imsha\Documents\Projects\DataValuator\backend\data\db\dataValuator.db',
    r'd:\Users\imsha\Documents\Projects\DataValuator\DataValuator.db',
]

found_something = False
for db_path in db_paths:
    if os.path.exists(db_path):
        print(f'\nChecking {db_path}...')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [r[1] for r in cursor.fetchall() if r[2] in ('TEXT', 'VARCHAR')]
                
                for col in columns:
                    query = f"SELECT * FROM {table} WHERE {col} LIKE '%titanic%' COLLATE NOCASE"
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    if rows:
                        print(f'  Found in table {table}, column {col}:')
                        for row in rows:
                            print(f'    {row}')
                        found_something = True
            conn.close()
        except Exception as e:
            print(f'Error reading {db_path}: {e}')

if not found_something:
    print('\nNo references to titanic found in any of the databases.')
