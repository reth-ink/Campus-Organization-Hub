import csv
from datetime import datetime
from ..models import Announcement, OfficerRole, Membership, User
from ..database import db
from .errors import AppError
import os
from sqlalchemy.exc import SQLAlchemyError

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
ANNOUNCEMENT_CSV = os.path.join(DATA_FOLDER, 'sample_announcements.csv')


class AnnouncementService:

    @staticmethod
    def create_announcement(org_id: int, user_id: int, title: str, content: str):
        try:
            membership = Membership.query.filter_by(UserID=user_id, OrgID=org_id, Status='Approved').first()
            if not membership:
                raise AppError("User is not a member of this organization", code='ACCESS_DENIED', http_status=403)

            officer = OfficerRole.query.filter_by(MembershipID=membership.MembershipID).first()
            if not officer:
                raise AppError("Only officers can create announcements", code='ACCESS_DENIED', http_status=403)

            announcement = Announcement(
                OrgID=org_id,
                CreatedBy=officer.OfficerRoleID,
                Title=title,
                Content=content,
                DatePosted=datetime.utcnow()
            )
            db.session.add(announcement)
            db.session.commit()
            return announcement

        except SQLAlchemyError as e:
            db.session.rollback()
            raise AppError(f"Database error creating announcement: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def get_org_announcements(org_id: int):
        try:
            announcements = Announcement.query.filter_by(OrgID=org_id).order_by(Announcement.DatePosted.desc()).all()
            result = []
            for ann in announcements:
                officer = OfficerRole.query.get(ann.CreatedBy)
                user = User.query.get(officer.Membership.UserID) if officer else None
                result.append({
                    "AnnouncementID": ann.AnnouncementID,
                    "Title": ann.Title,
                    "Content": ann.Content,
                    "DatePosted": ann.DatePosted,
                    "CreatorName": f"{user.FirstName} {user.LastName}" if user else "Unknown"
                })
            return result
        except SQLAlchemyError as e:
            raise AppError(f"Database error fetching announcements: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def announcement_to_dict(announcement: Announcement):
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
                    existing = Announcement.query.filter_by(Title=row['Title']).first()
                    if existing:
                        continue

                    date_posted = datetime.fromisoformat(row['DatePosted']) if row.get('DatePosted') else datetime.utcnow()
                    announcement = Announcement(
                        OrgID=int(row['OrgID']),
                        CreatedBy=int(row['CreatedBy']),
                        Title=row['Title'],
                        Content=row.get('Content', ''),
                        DatePosted=date_posted
                    )
                    db.session.add(announcement)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing announcements CSV: {str(e)}", code='CSV_ERROR', http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            announcements = Announcement.query.all()
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
