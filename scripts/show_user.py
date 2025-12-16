import sqlite3
import sys

if len(sys.argv) > 1:
    uid = sys.argv[1]
else:
    print('Usage: show_user.py <UserID>')
    sys.exit(1)

DB='campus_hub.db'
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()
row = cur.execute('SELECT UserID, FirstName, LastName, Email, created_at FROM users WHERE UserID=?', (uid,)).fetchone()
if row:
    print(dict(row))
else:
    print('no such user', uid)
conn.close()
