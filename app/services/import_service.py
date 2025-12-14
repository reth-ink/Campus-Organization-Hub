import os
import csv
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from ..database import db
from .errors import AppError
from ..models import User, Organization, Membership, OfficerRole, Announcement, Event

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

CSV_FILES = {
    "users": os.path.join(DATA_FOLDER, 'users.csv'),
    "organizations": os.path.join(DATA_FOLDER, 'organizations.csv'),
    "membership": os.path.join(DATA_FOLDER, 'membership.csv'),
    "officer_roles": os.path.join(DATA_FOLDER, 'officer role.csv'),
    "announcements": os.path.join(DATA_FOLDER, 'announcements.csv'),
    "events": os.path.join(DATA_FOLDER, 'events.csv')
}

class ImportService:

    @staticmethod
    def import_users():
        path = CSV_FILES['users']
        if not os.path.exists(path):
            print("Users CSV not found:", path)
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('UserID') or not row.get('Email'):
                    print("Skipping user row (missing UserID or Email):", row)
                    continue
                exists = db.session.execute(
                    text(f"SELECT 1 FROM {User.__tablename__} WHERE UserID = :uid"),
                    {"uid": row['UserID']}
                ).fetchone()
                if exists:
                    continue
                db.session.add(User(
                    UserID=int(row['UserID']),
                    FirstName=row.get('FirstName', ''),
                    LastName=row.get('LastName', ''),
                    Email=row.get('Email', ''),
                    PasswordHash=generate_password_hash('changeme'),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()
        print("Users imported successfully.")

    @staticmethod
    def import_organizations():
        path = CSV_FILES['organizations']
        if not os.path.exists(path):
            print("Organizations CSV not found:", path)
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OrgID') or not row.get('OrgName'):
                    print("Skipping organization row (missing OrgID or OrgName):", row)
                    continue
                exists = db.session.execute(
                    text(f"SELECT 1 FROM {Organization.__tablename__} WHERE OrgID = :oid"),
                    {"oid": row['OrgID']}
                ).fetchone()
                if exists:
                    continue
                db.session.add(Organization(
                    OrgID=int(row['OrgID']),
                    OrgName=row['OrgName'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()
        print("Organizations imported successfully.")

    @staticmethod
    def import_membership():
        path = CSV_FILES['membership']
        if not os.path.exists(path):
            print("Membership CSV not found:", path)
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('MembershipID') or not row.get('UserID') or not row.get('OrgID'):
                    print("Skipping membership row (missing IDs):", row)
                    continue
                user_exists = db.session.execute(
                    text(f"SELECT 1 FROM {User.__tablename__} WHERE UserID = :uid"),
                    {"uid": row['UserID']}
                ).fetchone()
                org_exists = db.session.execute(
                    text(f"SELECT 1 FROM {Organization.__tablename__} WHERE OrgID = :oid"),
                    {"oid": row['OrgID']}
                ).fetchone()
                if not user_exists:
                    print(f"Skipping MembershipID {row['MembershipID']} - UserID {row['UserID']} not found")
                    continue
                if not org_exists:
                    print(f"Skipping MembershipID {row['MembershipID']} - OrgID {row['OrgID']} not found")
                    continue
                exists = db.session.execute(
                    text(f"SELECT 1 FROM {Membership.__tablename__} WHERE MembershipID = :mid"),
                    {"mid": row['MembershipID']}
                ).fetchone()
                if exists:
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
        print("Memberships imported successfully.")

    @staticmethod
    def import_officer_roles():
        path = CSV_FILES['officer_roles']
        if not os.path.exists(path):
            print("OfficerRole CSV not found:", path)
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OfficerRoleID') or not row.get('MembershipID') or not row.get('RoleName'):
                    print("Skipping officer role row (missing IDs or RoleName):", row)
                    continue
                membership_exists = db.session.execute(
                    text(f"SELECT 1 FROM {Membership.__tablename__} WHERE MembershipID = :mid"),
                    {"mid": row['MembershipID']}
                ).fetchone()
                if not membership_exists:
                    print(f"Skipping OfficerRoleID {row['OfficerRoleID']} - MembershipID {row['MembershipID']} not found")
                    continue
                exists = db.session.execute(
                    text(f"SELECT 1 FROM {OfficerRole.__tablename__} WHERE OfficerRoleID = :rid"),
                    {"rid": row['OfficerRoleID']}
                ).fetchone()
                if exists:
                    continue
                db.session.add(OfficerRole(
                    OfficerRoleID=int(row['OfficerRoleID']),
                    MembershipID=int(row['MembershipID']),
                    RoleName=row['RoleName'],
                    RoleStart=datetime.strptime(row['RoleStart'], '%Y-%m-%d') if row.get('RoleStart') else None,
                    RoleEnd=datetime.strptime(row['RoleEnd'], '%Y-%m-%d') if row.get('RoleEnd') else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()
        print("Officer roles imported successfully.")

    @staticmethod
    def import_announcements():
        path = CSV_FILES['announcements']
        if not os.path.exists(path):
            print("Announcements CSV not found:", path)
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OrgID') or not row.get('CreatedBy'):
                    print("Skipping announcement row (missing OrgID or CreatedBy):", row)
                    continue
                org_exists = db.session.execute(
                    text(f"SELECT 1 FROM {Organization.__tablename__} WHERE OrgID = :oid"),
                    {"oid": int(row['OrgID'])}
                ).fetchone()
                officer_exists = db.session.execute(
                    text(f"SELECT 1 FROM {OfficerRole.__tablename__} WHERE OfficerRoleID = :rid"),
                    {"rid": int(row['CreatedBy'])}
                ).fetchone()
                if not org_exists:
                    print(f"Skipping AnnouncementID {row.get('AnnouncementID')} - OrgID {row['OrgID']} not found")
                    continue
                if not officer_exists:
                    print(f"Skipping AnnouncementID {row.get('AnnouncementID')} - OfficerRoleID {row['CreatedBy']} not found")
                    continue
                db.session.add(Announcement(
                    OrgID=int(row['OrgID']),
                    CreatedBy=int(row['CreatedBy']),
                    Title=row.get('Title', ''),
                    Content=row.get('Content', ''),
                    DatePosted=datetime.strptime(row['DatePosted'], '%Y-%m-%d') if row.get('DatePosted') else datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()
        print("Announcements imported successfully.")

    @staticmethod
    def import_events():
        path = CSV_FILES['events']
        if not os.path.exists(path):
            print("Events CSV not found:", path)
            return
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('OrgID') or not row.get('CreatedBy'):
                    print("Skipping event row (missing OrgID or CreatedBy):", row)
                    continue
                org_exists = db.session.execute(
                    text(f"SELECT 1 FROM {Organization.__tablename__} WHERE OrgID = :oid"),
                    {"oid": int(row['OrgID'])}
                ).fetchone()
                officer_exists = db.session.execute(
                    text(f"SELECT 1 FROM {OfficerRole.__tablename__} WHERE OfficerRoleID = :rid"),
                    {"rid": int(row['CreatedBy'])}
                ).fetchone()
                if not org_exists:
                    print(f"Skipping EventID {row.get('EventID')} - OrgID {row['OrgID']} not found")
                    continue
                if not officer_exists:
                    print(f"Skipping EventID {row.get('EventID')} - OfficerRoleID {row['CreatedBy']} not found")
                    continue
                db.session.add(Event(
                    OrgID=int(row['OrgID']),
                    CreatedBy=int(row['CreatedBy']),
                    EventName=row.get('EventName', ''),
                    EventDescription=row.get('EventDescription', ''),
                    EventDate=datetime.strptime(row['EventDate'], '%Y-%m-%d') if row.get('EventDate') else datetime.utcnow(),
                    Location=row.get('Location', ''),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        db.session.commit()
        print("Events imported successfully.")

    @staticmethod
    def import_all():
        ImportService.import_users()
        ImportService.import_organizations()
        ImportService.import_membership()
        ImportService.import_officer_roles()
        ImportService.import_announcements()
        ImportService.import_events()
        print("All data imported successfully.")
