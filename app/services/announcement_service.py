import csv
import os
from datetime import datetime
from sqlalchemy import text
from ..database import db
from .errors import AppError
from ..models import Announcement

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
ANNOUNCEMENT_CSV = os.path.join(DATA_FOLDER, 'announcements.csv')

class AnnouncementService:

    @staticmethod
    def import_from_csv():
        if not os.path.exists(ANNOUNCEMENT_CSV):
            return

        try:
            with open(ANNOUNCEMENT_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip if OrgID or CreatedBy missing
                    if not row.get('OrgID') or not row.get('CreatedBy'):
                        continue

                    # Convert IDs to int
                    try:
                        org_id = int(row['OrgID'])
                        created_by = int(row['CreatedBy'])
                    except ValueError:
                        print(f"Skipping announcement with invalid IDs: {row}")
                        continue

                    # Check if organization exists
                    org_exists = db.session.execute(
                        text("SELECT 1 FROM organizations WHERE OrgID = :oid"),
                        {"oid": org_id}
                    ).fetchone()
                    if not org_exists:
                        print(f"Skipping announcement: OrgID {org_id} does not exist")
                        continue

                    # Check if officer role exists
                    role_exists = db.session.execute(
                        text("SELECT 1 FROM officer_roles WHERE OfficerRoleID = :rid"),
                        {"rid": created_by}
                    ).fetchone()
                    if not role_exists:
                        print(f"Skipping announcement: OfficerRoleID {created_by} does not exist")
                        continue

                    # Parse DatePosted
                    date_posted = datetime.utcnow()
                    if row.get('DatePosted'):
                        try:
                            date_posted = datetime.strptime(row['DatePosted'], '%Y-%m-%d')
                        except ValueError:
                            print(f"Invalid DatePosted, using UTC now: {row['DatePosted']}")

                    # Create Announcement
                    announcement = Announcement(
                        OrgID=org_id,
                        CreatedBy=created_by,
                        Title=row.get('Title', ''),
                        Content=row.get('Content', ''),
                        DatePosted=date_posted,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(announcement)

            db.session.commit()
            print("Announcements imported successfully.")

        except Exception as e:
            db.session.rollback()
            raise AppError(
                f"Error importing announcements CSV: {str(e)}",
                code="CSV_ERROR",
                http_status=500
            )
