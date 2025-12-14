import csv
import os
from datetime import datetime
from ..database import db
from .errors import AppError
from sqlalchemy import text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
MEMBERSHIP_CSV = os.path.join(DATA_FOLDER, 'memberships.csv')


class MembershipService:

    @staticmethod
    def create_membership(user_id: int, org_id: int, status='Pending', date_applied=None, date_approved=None):
        if not user_id or not org_id:
            raise AppError("User ID and Organization ID are required",
                           code="INVALID_INPUT", http_status=400)
        try:
            now = datetime.utcnow()
            date_applied = date_applied or now
            insert_sql = text("""
                INSERT INTO memberships
                (UserID, OrgID, Status, DateApplied, DateApproved, created_at, updated_at)
                VALUES (:user_id, :org_id, :status, :date_applied, :date_approved, :created_at, :updated_at)
            """)
            db.session.execute(insert_sql, {
                "user_id": user_id,
                "org_id": org_id,
                "status": status,
                "date_applied": date_applied,
                "date_approved": date_approved,
                "created_at": now,
                "updated_at": now
            })
            db.session.commit()

            membership_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
            return db.session.execute(
                text("SELECT * FROM memberships WHERE MembershipID = :id"),
                {"id": membership_id}
            ).fetchone()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Database error creating membership: {str(e)}",
                           code="DB_ERROR", http_status=500)

    @staticmethod
    def get_memberships():
        try:
            sql = text("SELECT * FROM memberships ORDER BY MembershipID")
            return db.session.execute(sql).fetchall()
        except Exception as e:
            raise AppError(f"Database error fetching memberships: {str(e)}",
                           code="DB_ERROR", http_status=500)

    @staticmethod
    def membership_to_dict(membership):
        return {
            "MembershipID": membership.MembershipID,
            "UserID": membership.UserID,
            "OrgID": membership.OrgID,
            "Status": membership.Status,
            "DateApplied": membership.DateApplied.isoformat() if membership.DateApplied else None,
            "DateApproved": membership.DateApproved.isoformat() if membership.DateApproved else None
        }

    # ---------------- CSV IMPORT / EXPORT ----------------

    @staticmethod
    def import_from_csv():
        if not os.path.exists(MEMBERSHIP_CSV):
            raise AppError(f"{MEMBERSHIP_CSV} not found",
                           code="CSV_ERROR", http_status=500)
        try:
            with open(MEMBERSHIP_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required_fields = ['MembershipID', 'UserID', 'OrgID', 'Status', 'DateApplied', 'DateApproved']
                for field in required_fields:
                    if field not in reader.fieldnames:
                        raise AppError(f"CSV missing required column: {field}",
                                       code="CSV_ERROR", http_status=500)

                for row in reader:
                    # Skip existing memberships
                    exists_sql = text("SELECT 1 FROM memberships WHERE MembershipID = :mid")
                    if db.session.execute(exists_sql, {"mid": int(row['MembershipID'])}).fetchone():
                        continue

                    date_applied = datetime.fromisoformat(row['DateApplied']) if row.get('DateApplied') else None
                    date_approved = datetime.fromisoformat(row['DateApproved']) if row.get('DateApproved') else None

                    insert_sql = text("""
                        INSERT INTO memberships
                        (MembershipID, UserID, OrgID, Status, DateApplied, DateApproved, created_at, updated_at)
                        VALUES (:MembershipID, :UserID, :OrgID, :Status, :DateApplied, :DateApproved, :created_at, :updated_at)
                    """)
                    now = datetime.utcnow()
                    db.session.execute(insert_sql, {
                        "MembershipID": int(row['MembershipID']),
                        "UserID": int(row['UserID']),
                        "OrgID": int(row['OrgID']),
                        "Status": row.get('Status', ''),
                        "DateApplied": date_applied,
                        "DateApproved": date_approved,
                        "created_at": now,
                        "updated_at": now
                    })

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing memberships CSV: {str(e)}",
                           code="CSV_ERROR", http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            sql = text("SELECT * FROM memberships ORDER BY MembershipID")
            memberships = db.session.execute(sql).fetchall()
            with open(MEMBERSHIP_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['MembershipID', 'UserID', 'OrgID', 'Status', 'DateApplied', 'DateApproved'])
                writer.writeheader()
                for m in memberships:
                    writer.writerow({
                        'MembershipID': m.MembershipID,
                        'UserID': m.UserID,
                        'OrgID': m.OrgID,
                        'Status': m.Status,
                        'DateApplied': m.DateApplied.isoformat() if m.DateApplied else '',
                        'DateApproved': m.DateApproved.isoformat() if m.DateApproved else ''
                    })
        except Exception as e:
            raise AppError(f"Error exporting memberships CSV: {str(e)}",
                           code="CSV_ERROR", http_status=500)
