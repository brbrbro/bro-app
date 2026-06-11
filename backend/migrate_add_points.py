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

    if not table_exists(cur, 'exchange_records'):
        cur.execute('''
            CREATE TABLE exchange_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                cost INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("Created exchange_records")

    if not table_exists(cur, 'invitations'):
        cur.execute('''
            CREATE TABLE invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inviter_id INTEGER NOT NULL,
                invitee_id INTEGER NOT NULL UNIQUE,
                invite_code VARCHAR(50) NOT NULL,
                points_awarded INTEGER DEFAULT 50,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inviter_id) REFERENCES users(id),
                FOREIGN KEY (invitee_id) REFERENCES users(id)
            )
        ''')
        print("Created invitations")

    if not table_exists(cur, 'lexicon_words'):
        cur.execute('''
            CREATE TABLE lexicon_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word VARCHAR(100) NOT NULL,
                definition TEXT NOT NULL,
                example TEXT,
                subject VARCHAR(50) DEFAULT '通用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Created lexicon_words")

    if not table_exists(cur, 'notifications'):
        cur.execute('''
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type VARCHAR(20) DEFAULT 'system',
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cur.execute("INSERT INTO notifications (user_id, type, title, content) VALUES (NULL, 'system', ?, ?)",
                    ('欢迎使用 BRO', '一起开启刷题之旅吧！'))
        cur.execute("INSERT INTO notifications (user_id, type, title, content) VALUES (NULL, 'tip', ?, ?)",
                    ('小贴士', '每日签到可领取积分，连续签到奖励更多'))
        print("Created notifications + seeded 2 system messages")

    if not table_exists(cur, 'study_sessions'):
        cur.execute('''
            CREATE TABLE study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                seconds INTEGER NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("Created study_sessions")

    conn.commit()
    conn.close()
    print("Migration done.")

if __name__ == '__main__':
    main()
