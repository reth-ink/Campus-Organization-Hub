import sqlite3
import sys

DB_PATH = 'campus_hub.db'

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    return column in cols

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    table = 'officer_roles'
    added = []
    try:
        for col, default in [
            ('can_post_announcements', 0),
            ('can_create_events', 0),
            ('can_approve_members', 0),
            ('can_assign_roles', 0),
        ]:
            if not column_exists(cur, table, col):
                print(f"Adding column {col} to {table}")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} INTEGER DEFAULT {default}")
                added.append(col)
            else:
                print(f"Column {col} already exists")
        conn.commit()
        print("Migration complete. Added:", added)
    except Exception as e:
        print("Migration failed:", e)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
