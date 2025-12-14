import csv
import os
from datetime import datetime
from sqlalchemy import text
from ..database import db
from .errors import AppError
from ..models import Organization

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
ORG_CSV = os.path.join(DATA_FOLDER, 'organizations.csv')

class OrgService:

    @staticmethod
    def import_from_csv():
        if not os.path.exists(ORG_CSV):
            return

        try:
            with open(ORG_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip if OrgName missing
                    if not row.get('OrgName'):
                        continue

                    # Check if org already exists
                    exists = db.session.execute(
                        text("SELECT 1 FROM organizations WHERE OrgName = :name"),
                        {"name": row['OrgName']}
                    ).fetchone()
                    if exists:
                        continue

                    # Create new Organization
                    org = Organization(
                        OrgName=row['OrgName'],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(org)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(
                f"Error importing organizations CSV: {str(e)}",
                code="CSV_ERROR",
                http_status=500
            )
