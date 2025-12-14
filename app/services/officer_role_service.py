from sqlalchemy import text
import csv
import os
from sqlalchemy.exc import SQLAlchemyError
from ..models import OfficerRole
from ..database import db
from .errors import AppError

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
OFFICER_ROLE_CSV = os.path.join(DATA_FOLDER, 'officer_roles.csv')


class OfficerRoleService:

    @staticmethod
    def import_from_csv():
        if not os.path.exists(OFFICER_ROLE_CSV):
            raise AppError(f"{OFFICER_ROLE_CSV} not found", code="CSV_ERROR", http_status=500)

        try:
            with open(OFFICER_ROLE_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    role_name = row.get('RoleName')
                    if not role_name:
                        continue

                    # Skip if role already exists
                    exists_sql = text("SELECT 1 FROM officer_roles WHERE RoleName = :name")
                    if db.session.execute(exists_sql, {"name": role_name}).fetchone():
                        continue

                    role = OfficerRole(
                        RoleName=role_name,
                        Description=row.get('Description', '')
                    )
                    db.session.add(role)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing officer roles CSV: {str(e)}", code="CSV_ERROR", http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            roles = db.session.query(OfficerRole).order_by(OfficerRole.OfficerRoleID).all()
            with open(OFFICER_ROLE_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['RoleName', 'Description'])
                writer.writeheader()
                for r in roles:
                    writer.writerow({
                        'RoleName': r.RoleName,
                        'Description': r.Description
                    })
        except Exception as e:
            raise AppError(f"Error exporting officer roles CSV: {str(e)}", code="CSV_ERROR", http_status=500)
