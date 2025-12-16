import sqlite3, os
db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'campus_hub.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT MembershipID,UserID,OrgID,Status FROM memberships WHERE OrgID=7")
rows = cur.fetchall()
print(rows)
conn.close()
