"""一次性脚本：给已存在的 SQLite 数据库添加新字段和新表。
首次部署时如果是空数据库，db.create_all() 会自动建表，不需要本脚本。
"""
import sqlite3
import os

DB_PATH = 'C:/bro-dev/bro.db'

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None

def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}, skip migration; db.create_all() will handle a fresh DB.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if not table_exists(cur, 'users'):
        print("users table not found; db.create_all() will handle a fresh DB.")
        conn.close()
        return

    for col, default in [('points', 0), ('exp', 0), ('level', 1)]:
        if not column_exists(cur, 'users', col):
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default}")
            print(f"Added users.{col}")

    if not table_exists(cur, 'daily_checkins'):
        cur.execute('''
            CREATE TABLE daily_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                check_date DATE NOT NULL,
                points_awarded INTEGER DEFAULT 10,
                exp_awarded INTEGER DEFAULT 5,
                streak INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, check_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("Created daily_checkins")

    conn.commit()
    conn.close()
    print("Migration done.")

if __name__ == '__main__':
    main()
