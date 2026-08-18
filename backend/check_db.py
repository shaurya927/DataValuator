import sqlite3

def check_db():
    conn = sqlite3.connect('data/db/dataValuator.db')
    c = conn.cursor()
    c.execute("SELECT id, status, model_name FROM training_runs ORDER BY started_at DESC LIMIT 5")
    for row in c.fetchall():
        print(row)
        
if __name__ == '__main__':
    check_db()
