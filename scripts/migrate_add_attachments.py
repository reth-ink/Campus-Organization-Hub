#!/usr/bin/env python3
"""
Simple migration helper to add an Attachments column to the announcements table
if it doesn't already exist. Creates a timestamped backup of the DB first.

Run from the project root (where campus_hub.db lives):
    py scripts\migrate_add_attachments.py

This script is safe to run multiple times.
"""
import sqlite3
import shutil
import os
import sys
from datetime import datetime

DB = "campus_hub.db"


def main():
    cwd = os.getcwd()
    db_path = os.path.join(cwd, DB)

    if not os.path.exists(db_path):
        print(f"ERROR: database file not found at {db_path}")
        sys.exit(2)

    # Create a backup
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{db_path}.backup_{ts}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute("PRAGMA table_info('announcements');")
        rows = cur.fetchall()
        cols = [r[1] for r in rows]

        if 'Attachments' in cols:
            print("Column 'Attachments' already exists on announcements. Nothing to do.")
            return

        print("Adding 'Attachments' TEXT column to announcements table...")
        cur.execute("ALTER TABLE announcements ADD COLUMN Attachments TEXT;")
        conn.commit()
        print("Column added successfully.")

        # show resulting schema info for announcements
        cur.execute("PRAGMA table_info('announcements');")
        for r in cur.fetchall():
            print(r)

    except sqlite3.DatabaseError as e:
        print("Database error:", e)
        sys.exit(3)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
