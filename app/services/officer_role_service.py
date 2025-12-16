import csv
from flask import current_app
from ..database import get_db
from ..models.officer_role import OfficerRole
from ..utils.errors import AppError

class OfficerRoleService:

    @staticmethod
    def create_officer_role(name, permissions):
        db = get_db()
        try:
            # officer_roles table in schema_v1 uses MembershipID, RoleName, RoleStart, RoleEnd
            db.execute(
                'INSERT INTO officer_roles (MembershipID, RoleName, StartDate, EndDate) VALUES (?, ?, ?, ?)',
                (None, name, None, None)
            )
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create officer role: {str(e)}')

    @staticmethod
    def get_all_officer_roles():
        db = get_db()
        # select canonical columns from schema (StartDate/EndDate) — model accepts these
        rows = db.execute('SELECT OfficerRoleID, MembershipID, RoleName, StartDate, EndDate FROM officer_roles').fetchall()
        return [OfficerRole(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def import_officer_roles_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for r in reader:
                    # CSV uses OfficerRoleID, MembershipID, RoleName, RoleStart, RoleEnd
                    membership = r.get('MembershipID') or r.get('membership_id')
                    role_name = r.get('RoleName') or r.get('name')
                    role_start = r.get('StartDate') or r.get('RoleStart')
                    role_end = r.get('EndDate') or r.get('RoleEnd')
                    try:
                        db = get_db()
                        db.execute('INSERT OR IGNORE INTO officer_roles (OfficerRoleID, MembershipID, RoleName, StartDate, EndDate) VALUES (?, ?, ?, ?, ?)',
                                   (r.get('OfficerRoleID'), membership, role_name, role_start, role_end))
                        db.commit()
                    except Exception as e:
                        raise AppError('DB_ERROR', f'Could not create officer role from CSV: {str(e)}')
        except Exception as e:
            raise AppError('CSV_IMPORT_ERROR', f'Error importing CSV: {str(e)}')