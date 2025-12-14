import csv
import os
from sqlalchemy.exc import SQLAlchemyError
from ..models import Organization
from ..database import db
from .errors import AppError

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
ORG_CSV = os.path.join(DATA_FOLDER, 'organizations.csv')


class OrgService:

    @staticmethod
    def create_org(name: str, description: str, creator_id: int):
        if not name or not description:
            raise AppError("Name and description are required", code="INVALID_INPUT", http_status=400)

        try:
            org = Organization(
                OrgName=name,
                Description=description
            )
            db.session.add(org)
            db.session.commit()
            return org

        except SQLAlchemyError as e:
            db.session.rollback()
            raise AppError(f"Database error creating organization: {str(e)}", code="DB_ERROR", http_status=500)

    @staticmethod
    def search_orgs():
        try:
            return Organization.query.order_by(Organization.OrgName).all()
        except SQLAlchemyError as e:
            raise AppError(f"Database error fetching organizations: {str(e)}", code="DB_ERROR", http_status=500)

    @staticmethod
    def get_org(org_id: int):
        try:
            org = Organization.query.get(org_id)
            if not org:
                raise AppError("Organization not found", code="NOT_FOUND", http_status=404)
            return org
        except SQLAlchemyError as e:
            raise AppError(f"Database error fetching organization: {str(e)}", code="DB_ERROR", http_status=500)

    @staticmethod
    def org_to_dict(org: Organization):
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
                    if Organization.query.filter_by(OrgName=row['OrgName']).first():
                        continue

                    org = Organization(
                        OrgName=row['OrgName'],
                        Description=row.get('OrgDescription', '')
                    )
                    db.session.add(org)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing organizations CSV: {str(e)}", code="CSV_ERROR", http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            orgs = Organization.query.order_by(Organization.OrgID).all()

            with open(ORG_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['OrgName', 'OrgDescription']
                )
                writer.writeheader()

                for org in orgs:
                    writer.writerow({
                        'OrgName': org.OrgName,
                        'OrgDescription': org.Description
                    })

        except Exception as e:
            raise AppError(f"Error exporting organizations CSV: {str(e)}", code="CSV_ERROR", http_status=500)
