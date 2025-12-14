import csv
import os
from datetime import datetime
from sqlalchemy import text
from ..database import db
from .errors import AppError

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
ORG_CSV = os.path.join(DATA_FOLDER, 'organizations.csv')


class OrgService:

    @staticmethod
    def create_org(name: str, description: str, creator_id: int = None):
        if not name or not description:
            raise AppError("Name and description are required", code="INVALID_INPUT", http_status=400)

        try:
            sql = text("""
                INSERT INTO organizations (OrgName, Description, created_at, updated_at)
                VALUES (:OrgName, :Description, :created_at, :updated_at)
            """)
            now = datetime.utcnow()
            db.session.execute(sql, {
                "OrgName": name,
                "Description": description,
                "created_at": now,
                "updated_at": now
            })
            db.session.commit()

            org_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
            return db.session.execute(text("SELECT * FROM organizations WHERE OrgID = :id"), {"id": org_id}).fetchone()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Database error creating organization: {str(e)}", code="DB_ERROR", http_status=500)

    @staticmethod
    def search_orgs():
        try:
            sql = text("SELECT * FROM organizations ORDER BY OrgName")
            return db.session.execute(sql).fetchall()
        except Exception as e:
            raise AppError(f"Database error fetching organizations: {str(e)}", code="DB_ERROR", http_status=500)

    @staticmethod
    def get_org(org_id: int):
        try:
            sql = text("SELECT * FROM organizations WHERE OrgID = :id")
            org = db.session.execute(sql, {"id": org_id}).fetchone()
            if not org:
                raise AppError("Organization not found", code="NOT_FOUND", http_status=404)
            return org
        except Exception as e:
            raise AppError(f"Database error fetching organization: {str(e)}", code="DB_ERROR", http_status=500)

    @staticmethod
    def org_to_dict(org):
        return {
            "id": org.OrgID,
            "name": org.OrgName,
            "description": org.Description
        }

    # ---------------- CSV IMPORT / EXPORT ----------------

    @staticmethod
    def import_from_csv():
        if not os.path.exists(ORG_CSV):
            raise AppError(f"{ORG_CSV} not found", code="CSV_ERROR", http_status=500)

        try:
            with open(ORG_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    org_name = row.get('OrgName')
                    if not org_name:
                        continue

                    # Check if organization already exists
                    check_sql = text("SELECT 1 FROM organizations WHERE OrgName = :name")
                    exists = db.session.execute(check_sql, {"name": org_name}).fetchone()
                    if exists:
                        continue

                    insert_sql = text("""
                        INSERT INTO organizations (OrgName, Description, created_at, updated_at)
                        VALUES (:OrgName, :Description, :created_at, :updated_at)
                    """)
                    now = datetime.utcnow()
                    db.session.execute(insert_sql, {
                        "OrgName": org_name,
                        "Description": row.get('OrgDescription', ''),
                        "created_at": now,
                        "updated_at": now
                    })

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing organizations CSV: {str(e)}", code="CSV_ERROR", http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            orgs = db.session.execute(text("SELECT * FROM organizations ORDER BY OrgID")).fetchall()

            with open(ORG_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['OrgName', 'OrgDescription'])
                writer.writeheader()

                for org in orgs:
                    writer.writerow({
                        'OrgName': org.OrgName,
                        'OrgDescription': org.Description
                    })

        except Exception as e:
            raise AppError(f"Error exporting organizations CSV: {str(e)}", code="CSV_ERROR", http_status=500)
