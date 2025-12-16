import sqlite3, os

db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'campus_hub.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute('''SELECT officer_roles.OfficerRoleID, officer_roles.MembershipID, officer_roles.RoleName, memberships.UserID, users.FirstName, users.LastName
FROM officer_roles
JOIN memberships ON officer_roles.MembershipID = memberships.MembershipID
JOIN users ON memberships.UserID = users.UserID
WHERE memberships.OrgID = 7''')
rows = cur.fetchall()
print(rows)
conn.close()
