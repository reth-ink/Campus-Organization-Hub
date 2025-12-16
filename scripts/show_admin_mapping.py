import sqlite3, os
db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'campus_hub.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT OfficerRoleID,MembershipID,RoleName FROM officer_roles WHERE lower(RoleName)='admin'")
rows = cur.fetchall()
print('admin roles:', rows)
for orow in rows:
    officer_id, mem_id, role = orow
    cur.execute('SELECT MembershipID, UserID, OrgID, Status FROM memberships WHERE MembershipID=?',(mem_id,))
    m = cur.fetchone()
    print('membership row for', mem_id, ':', m)
    if m:
        user_id = m[1]
        org_id = m[2]
        cur.execute('SELECT UserID, FirstName, LastName FROM users WHERE UserID=?',(user_id,))
        u = cur.fetchone()
        print('user:', u)
        cur.execute('SELECT OrgID, OrgName FROM organizations WHERE OrgID=?',(org_id,))
        o = cur.fetchone()
        print('org:', o)
conn.close()
