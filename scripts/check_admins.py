import sqlite3
import os
db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'campus_hub.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT OfficerRoleID,MembershipID,RoleName FROM officer_roles WHERE lower(RoleName)='admin'")
rows = cur.fetchall()
print(rows)
conn.close()
