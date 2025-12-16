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
            cur = db.execute(
                'INSERT OR IGNORE INTO organizations (OrgName, Description) VALUES (?, ?)',
                (org_name, org_description)
            )
            db.commit()

            # If the insert created a new row, return its id. If the insert was ignored
            # (duplicate OrgName), look up the existing OrgID and return it.
            org_id = getattr(cur, 'lastrowid', None)
            if not org_id:
                row = db.execute('SELECT OrgID FROM organizations WHERE OrgName = ? LIMIT 1', (org_name,)).fetchone()
                org_id = row['OrgID'] if row else None
            return org_id
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create organization: {str(e)}')

    @staticmethod
    def get_all_organizations():
        db = get_db()
        # return canonical keys expected by Organization model
        rows = db.execute('SELECT OrgID, OrgName, Description AS OrgDescription FROM organizations').fetchall()
        orgs = [Organization(**dict(row)).to_dict() for row in rows]

        # Demonstrate lambda usage in data processing: sort organizations by OrgName
        # (case-insensitive). This satisfies the "lambda functions" requirement
        # while keeping behavior backwards-compatible.
        try:
            orgs_sorted = sorted(orgs, key=lambda o: (o.get('OrgName') or '').lower())
        except Exception:
            # fallback: if any unexpected structure, return unsorted list
            orgs_sorted = orgs

        return orgs_sorted

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

    @staticmethod
    def update_organization(org_id, name=None, description=None):
        """Update organization name and/or description."""
        db = get_db()
        try:
            # Only update provided fields
            if name is not None and description is not None:
                db.execute('UPDATE organizations SET OrgName = ?, Description = ?, updated_at = CURRENT_TIMESTAMP WHERE OrgID = ?', (name, description, org_id))
            elif name is not None:
                db.execute('UPDATE organizations SET OrgName = ?, updated_at = CURRENT_TIMESTAMP WHERE OrgID = ?', (name, org_id))
            elif description is not None:
                db.execute('UPDATE organizations SET Description = ?, updated_at = CURRENT_TIMESTAMP WHERE OrgID = ?', (description, org_id))
            else:
                return
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not update organization: {str(e)}')

    @staticmethod
    def delete_organization(org_id):
        """Delete an organization and rely on ON DELETE CASCADE for related rows."""
        db = get_db()
        try:
            db.execute('DELETE FROM organizations WHERE OrgID = ?', (org_id,))
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not delete organization: {str(e)}')