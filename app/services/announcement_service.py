import csv
import os
from datetime import datetime
from ..database import db
from .errors import AppError
from sqlalchemy import text

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
ANNOUNCEMENT_CSV = os.path.join(DATA_FOLDER, 'sample_announcements.csv')


class AnnouncementService:

    @staticmethod
    def create_announcement(org_id: int, user_id: int, title: str, content: str):
        try:
            # Check membership
            membership_sql = text("""
                SELECT MembershipID FROM memberships
                WHERE UserID = :user_id AND OrgID = :org_id AND Status = 'Approved'
            """)
            membership = db.session.execute(membership_sql, {"user_id": user_id, "org_id": org_id}).fetchone()
            if not membership:
                raise AppError("User is not a member of this organization", code='ACCESS_DENIED', http_status=403)

            membership_id = membership.MembershipID

            # Check officer role
            officer_sql = text("SELECT OfficerRoleID FROM officer_roles WHERE MembershipID = :mid")
            officer = db.session.execute(officer_sql, {"mid": membership_id}).fetchone()
            if not officer:
                raise AppError("Only officers can create announcements", code='ACCESS_DENIED', http_status=403)

            officer_id = officer.OfficerRoleID

            # Insert announcement
            insert_sql = text("""
                INSERT INTO announcements
                (OrgID, CreatedBy, Title, Content, DatePosted, created_at, updated_at)
                VALUES (:org_id, :created_by, :title, :content, :date_posted, :created_at, :updated_at)
            """)
            now = datetime.utcnow()
            db.session.execute(insert_sql, {
                "org_id": org_id,
                "created_by": officer_id,
                "title": title,
                "content": content,
                "date_posted": now,
                "created_at": now,
                "updated_at": now
            })
            db.session.commit()

            # Return inserted announcement
            ann_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
            return db.session.execute(
                text("SELECT * FROM announcements WHERE AnnouncementID = :id"), {"id": ann_id}
            ).fetchone()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Database error creating announcement: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def get_org_announcements(org_id: int):
        try:
            sql = text("""
                SELECT a.AnnouncementID, a.Title, a.Content, a.DatePosted,
                       u.FirstName, u.LastName
                FROM announcements a
                JOIN officer_roles o ON a.CreatedBy = o.OfficerRoleID
                JOIN memberships m ON o.MembershipID = m.MembershipID
                JOIN users u ON m.UserID = u.UserID
                WHERE a.OrgID = :org_id
                ORDER BY a.DatePosted DESC
            """)
            rows = db.session.execute(sql, {"org_id": org_id}).fetchall()

            result = []
            for r in rows:
                result.append({
                    "AnnouncementID": r.AnnouncementID,
                    "Title": r.Title,
                    "Content": r.Content,
                    "DatePosted": r.DatePosted,
                    "CreatorName": f"{r.FirstName} {r.LastName}"
                })
            return result

        except Exception as e:
            raise AppError(f"Database error fetching announcements: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def announcement_to_dict(announcement):
        return {
            "id": announcement.AnnouncementID,
            "org_id": announcement.OrgID,
            "created_by": announcement.CreatedBy,
            "title": announcement.Title,
            "content": announcement.Content,
            "date_posted": announcement.DatePosted.isoformat() if announcement.DatePosted else None
        }

    # ---------------- CSV IMPORT / EXPORT ----------------
    @staticmethod
    def import_from_csv():
        if not os.path.exists(ANNOUNCEMENT_CSV):
            return
        try:
            with open(ANNOUNCEMENT_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get('Title'):
                        continue

                    # Check if announcement exists
                    existing_sql = text("SELECT 1 FROM announcements WHERE Title = :title")
                    if db.session.execute(existing_sql, {"title": row['Title']}).fetchone():
                        continue

                    date_posted = datetime.fromisoformat(row['DatePosted']) if row.get('DatePosted') else datetime.utcnow()

                    insert_sql = text("""
                        INSERT INTO announcements
                        (OrgID, CreatedBy, Title, Content, DatePosted, created_at, updated_at)
                        VALUES (:OrgID, :CreatedBy, :Title, :Content, :DatePosted, :created_at, :updated_at)
                    """)
                    db.session.execute(insert_sql, {
                        "OrgID": int(row['OrgID']),
                        "CreatedBy": int(row['CreatedBy']),
                        "Title": row['Title'],
                        "Content": row.get('Content', ''),
                        "DatePosted": date_posted,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing announcements CSV: {str(e)}", code='CSV_ERROR', http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            sql = text("SELECT * FROM announcements")
            announcements = db.session.execute(sql).fetchall()

            with open(ANNOUNCEMENT_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['OrgID', 'CreatedBy', 'Title', 'Content', 'DatePosted'])
                writer.writeheader()

                for ann in announcements:
                    writer.writerow({
                        'OrgID': ann.OrgID,
                        'CreatedBy': ann.CreatedBy,
                        'Title': ann.Title,
                        'Content': ann.Content,
                        'DatePosted': ann.DatePosted.isoformat() if ann.DatePosted else ''
                    })
        except Exception as e:
            raise AppError(f"Error exporting announcements CSV: {str(e)}", code='CSV_ERROR', http_status=500)
