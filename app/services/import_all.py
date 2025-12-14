import os
import csv
from datetime import datetime
from sqlalchemy import text
from ..database import db
from .errors import AppError
from ..models import User, Organization, Membership, OfficerRole, Announcement, Event
from werkzeug.security import generate_password_hash

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

CSV_FILES = {
    "users": os.path.join(DATA_FOLDER, 'users.csv'),
    "organizations": os.path.join(DATA_FOLDER, 'organizations.csv'),
    "membership": os.path.join(DATA_FOLDER, 'membership.csv'),
    "officer_roles": os.path.join(DATA_FOLDER, 'officer_role.csv'),
    "announcements": os.path.join(DATA_FOLDER, 'announcements.csv'),
    "events": os.path.join(DATA_FOLDER, 'events.csv')
}

class ImportService:

    @staticmethod
    def import_users():
        path = CSV_FILES['users']
        if not os.path.exists(path):
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('UserID') or not row.get('Email'):
                    continue
                exists = db.session.execute(
                    text("SELECT 1 FROM users WHERE UserID = :uid"), {"uid": row['UserID']}
                ).fetchone()
                if exists:
                    continue
                db.session.add(User(
                    UserID=int(row['UserID']),
                    FirstName=row.get('FirstName', ''),
                    LastName=row.get('LastName', ''),
                    Email=row.get('Email', ''),
                    PasswordHash=generate_password_hash("changeme123"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()

    @staticmethod
    def import_organizations():
        path = CSV_FILES['organizations']
        if not os.path.exists(path):
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OrgID') or not row.get('OrgName'):
                    continue
                exists = db.session.execute(
                    text("SELECT 1 FROM organizations WHERE OrgID = :oid"),
                    {"oid": row['OrgID']}
                ).fetchone()
                if exists:
                    continue
                db.session.add(Organization(
                    OrgID=int(row['OrgID']),
                    OrgName=row['OrgName'],
                    OrgDescription=row.get('OrgDescription', ''),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()

    @staticmethod
    def import_membership():
        path = CSV_FILES['membership']
        if not os.path.exists(path):
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('MembershipID') or not row.get('UserID') or not row.get('OrgID'):
                    continue
                exists = db.session.execute(
                    text("SELECT 1 FROM membership WHERE MembershipID = :mid"),
                    {"mid": row['MembershipID']}
                ).fetchone()
                if exists:
                    continue
                # Foreign keys check
                user_exists = db.session.execute(
                    text("SELECT 1 FROM users WHERE UserID = :uid"), {"uid": row['UserID']}
                ).fetchone()
                org_exists = db.session.execute(
                    text("SELECT 1 FROM organizations WHERE OrgID = :oid"), {"oid": row['OrgID']}
                ).fetchone()
                if not user_exists or not org_exists:
                    print(f"Skipping membership {row['MembershipID']}: User or Org missing")
                    continue
                db.session.add(Membership(
                    MembershipID=int(row['MembershipID']),
                    UserID=int(row['UserID']),
                    OrgID=int(row['OrgID']),
                    Status=row.get('Status', 'Approved'),
                    DateApplied=datetime.strptime(row['DateApplied'], '%Y-%m-%d') if row.get('DateApplied') else None,
                    DateApproved=datetime.strptime(row['DateApproved'], '%Y-%m-%d') if row.get('DateApproved') else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()

    @staticmethod
    def import_officer_roles():
        path = CSV_FILES['officer_roles']
        if not os.path.exists(path):
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OfficerRoleID') or not row.get('MembershipID'):
                    continue
                exists = db.session.execute(
                    text("SELECT 1 FROM officer_roles WHERE OfficerRoleID = :rid"),
                    {"rid": row['OfficerRoleID']}
                ).fetchone()
                if exists:
                    continue
                membership_exists = db.session.execute(
                    text("SELECT 1 FROM membership WHERE MembershipID = :mid"),
                    {"mid": row['MembershipID']}
                ).fetchone()
                if not membership_exists:
                    print(f"Skipping officer role {row['OfficerRoleID']}: Membership missing")
                    continue
                db.session.add(OfficerRole(
                    OfficerRoleID=int(row['OfficerRoleID']),
                    MembershipID=int(row['MembershipID']),
                    RoleName=row['RoleName'],
                    RoleStart=datetime.strptime(row['RoleStart'], '%Y-%m-%d') if row.get('RoleStart') else datetime.utcnow(),
                    RoleEnd=datetime.strptime(row['RoleEnd'], '%Y-%m-%d') if row.get('RoleEnd') else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()

    @staticmethod
    def import_announcements():
        path = CSV_FILES['announcements']
        if not os.path.exists(path):
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OrgID') or not row.get('CreatedBy'):
                    continue
                org_id = int(row['OrgID'])
                created_by = int(row['CreatedBy'])
                org_exists = db.session.execute(
                    text("SELECT 1 FROM organizations WHERE OrgID = :oid"), {"oid": org_id}
                ).fetchone()
                role_exists = db.session.execute(
                    text("SELECT 1 FROM officer_roles WHERE OfficerRoleID = :rid"), {"rid": created_by}
                ).fetchone()
                if not org_exists or not role_exists:
                    print(f"Skipping announcement: OrgID {org_id} or CreatedBy {created_by} missing")
                    continue
                date_posted = datetime.strptime(row['DatePosted'], '%Y-%m-%d') if row.get('DatePosted') else datetime.utcnow()
                db.session.add(Announcement(
                    OrgID=org_id,
                    CreatedBy=created_by,
                    Title=row.get('Title', ''),
                    Content=row.get('Content', ''),
                    DatePosted=date_posted,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()

    @staticmethod
    def import_events():
        path = CSV_FILES['events']
        if not os.path.exists(path):
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OrgID') or not row.get('CreatedBy'):
                    continue
                org_id = int(row['OrgID'])
                created_by = int(row['CreatedBy'])
                org_exists = db.session.execute(
                    text("SELECT 1 FROM organizations WHERE OrgID = :oid"), {"oid": org_id}
                ).fetchone()
                role_exists = db.session.execute(
                    text("SELECT 1 FROM officer_roles WHERE OfficerRoleID = :rid"), {"rid": created_by}
                ).fetchone()
                if not org_exists or not role_exists:
                    print(f"Skipping event: OrgID {org_id} or CreatedBy {created_by} missing")
                    continue
                event_date = datetime.strptime(row['EventDate'], '%Y-%m-%d') if row.get('EventDate') else datetime.utcnow()
                db.session.add(Event(
                    OrgID=org_id,
                    CreatedBy=created_by,
                    EventName=row.get('EventName', ''),
                    EventDescription=row.get('EventDescription', ''),
                    EventDate=event_date,
                    Location=row.get('Location', ''),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()

    @staticmethod
    def import_all():
        ImportService.import_users()
        ImportService.import_organizations()
        ImportService.import_membership()
        ImportService.import_officer_roles()
        ImportService.import_announcements()
        ImportService.import_events()
