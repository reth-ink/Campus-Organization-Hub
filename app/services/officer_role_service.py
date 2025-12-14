import csv
import os
from datetime import datetime
from sqlalchemy import text
from ..database import db
from .errors import AppError
from ..models import OfficerRole

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
OFFICER_ROLE_CSV = os.path.join(DATA_FOLDER, 'officer_role.csv')

class OfficerRoleService:

    @staticmethod
    def import_from_csv():
        if not os.path.exists(OFFICER_ROLE_CSV):
            return

        try:
            with open(OFFICER_ROLE_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get('MembershipID') or not row.get('RoleName'):
                        continue

                    membership_id = int(row['MembershipID'])

                    # Check if the referenced membership exists
                    membership_exists = db.session.execute(
                        text("SELECT 1 FROM memberships WHERE MembershipID = :mid"),
                        {"mid": membership_id}
                    ).fetchone()
                    if not membership_exists:
                        print(f"Skipping OfficerRole {row.get('RoleName')} - MembershipID {membership_id} not found")
                        continue

                    # Skip if officer role already exists
                    exists = db.session.execute(
                        text("SELECT 1 FROM officer_roles WHERE MembershipID = :mid AND RoleName = :role"),
                        {"mid": membership_id, "role": row['RoleName']}
                    ).fetchone()
                    if exists:
                        continue

                    # Parse dates
                    role_start = None
                    role_end = None
                    if row.get('RoleStart'):
                        try:
                            role_start = datetime.strptime(row['RoleStart'], "%Y-%m-%d")
                        except ValueError:
                            role_start = datetime.utcnow()
                    if row.get('RoleEnd'):
                        try:
                            role_end = datetime.strptime(row['RoleEnd'], "%Y-%m-%d")
                        except ValueError:
                            role_end = None

                    role = OfficerRole(
                        MembershipID=membership_id,
                        RoleName=row['RoleName'],
                        RoleStart=role_start or datetime.utcnow(),
                        RoleEnd=role_end,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(role)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(
                f"Error importing officer roles CSV: {str(e)}",
                code="CSV_ERROR",
                http_status=500
            )
