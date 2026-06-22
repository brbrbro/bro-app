import os
import sqlite3

DB_PATH = 'C:/bro-dev/bro.db'

COLUMNS = [
    ('source_page', 'INTEGER'),
    ('bbox', 'TEXT'),
    ('raw_ocr_text', 'TEXT'),
    ('formula_latex', 'TEXT'),
    ('formula_images', 'TEXT'),
    ('confidence_detail', 'TEXT')
]


def column_exists(cur, table, column):
    cur.execute(f'PRAGMA table_info({table})')
    return any(row[1] == column for row in cur.fetchall())


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        print('DB not found at C:/bro-dev/bro.db; app db.create_all() will create fresh schema')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parsed_questions'")
    if not cur.fetchone():
        print('parsed_questions table not found; app db.create_all() will create fresh schema')
        conn.close()
        return

    for name, sql_type in COLUMNS:
        if not column_exists(cur, 'parsed_questions', name):
            cur.execute(f'ALTER TABLE parsed_questions ADD COLUMN {name} {sql_type}')
            print(f'Added parsed_questions.{name}')

    conn.commit()
    conn.close()
    print('Import recognition migration done.')


if __name__ == '__main__':
    main()
