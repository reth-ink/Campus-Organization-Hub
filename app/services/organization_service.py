import csv
from flask import current_app
from ..database import get_db
from ..models.organization import Organization
from ..utils.errors import AppError

class OrgService:

    @staticmethod
    def create_organization(org_name, org_description):
        db = get_db()
        try:
            db.execute(
                'INSERT OR IGNORE INTO organizations (OrgName, Description) VALUES (?, ?)',
                (org_name, org_description)
            )
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create organization: {str(e)}')

    @staticmethod
    def get_all_organizations():
        db = get_db()
        # return canonical keys expected by Organization model
        rows = db.execute('SELECT OrgID, OrgName, Description AS OrgDescription FROM organizations').fetchall()
        return [Organization(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def import_organizations_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for o in reader:
                    # support CSV headers that use PascalCase (OrgName) or lowercase (name)
                    name = o.get('OrgName') or o.get('name')
                    desc = o.get('OrgDescription') or o.get('description')
                    OrgService.create_organization(name, desc)
        except Exception as e:
            raise AppError('CSV_IMPORT_ERROR', f'Error importing CSV: {str(e)}')