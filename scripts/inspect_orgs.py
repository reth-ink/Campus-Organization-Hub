import sqlite3
import sys

DB='campus_hub.db'
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()

print('Last 10 organizations:')
for row in cur.execute('SELECT OrgID, OrgName, Description, created_at FROM organizations ORDER BY OrgID DESC LIMIT 10'):
    print(dict(row))

print('\nLast 20 memberships:')
for row in cur.execute('SELECT MembershipID, UserID, OrgID, Status, DateApplied, DateApproved FROM memberships ORDER BY MembershipID DESC LIMIT 20'):
    print(dict(row))

print('\nLast 20 officer_roles:')
for row in cur.execute('SELECT OfficerRoleID, MembershipID, RoleName, can_post_announcements, can_create_events, can_approve_members, can_assign_roles FROM officer_roles ORDER BY OfficerRoleID DESC LIMIT 20'):
    print(dict(row))

conn.close()
