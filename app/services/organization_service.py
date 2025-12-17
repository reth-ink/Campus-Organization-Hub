import csv
import sqlite3
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
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while creating organization')
            raise AppError('DB_ERROR', 'Could not create organization', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while creating organization')
            raise AppError('DB_ERROR', 'Could not create organization', original_exception=e)

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
        except (TypeError, AttributeError, KeyError) as e:
            current_app.logger.debug('Could not sort organizations: %s', e)
            orgs_sorted = orgs
        except Exception as e:
            current_app.logger.exception('Unexpected error when sorting organizations')
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
                    try:
                        OrgService.create_organization(name, desc)
                    except AppError:
                        current_app.logger.exception('Failed to create organization from CSV row, continuing')
                        continue
        except (csv.Error, OSError) as e:
            current_app.logger.exception('Error reading organizations CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error importing organizations from CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)

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
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while updating organization')
            raise AppError('DB_ERROR', 'Could not update organization', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while updating organization')
            raise AppError('DB_ERROR', 'Could not update organization', original_exception=e)

    @staticmethod
    def delete_organization(org_id):
        """Delete an organization and remove related rows explicitly.

        Some SQLite setups may not have foreign key enforcement enabled, or the
        schema may have been created without ON DELETE CASCADE. To be robust we
        explicitly remove dependent rows in the right order:

        1. announcements (reference OrgID, may reference officer_roles)
        2. events (reference OrgID, may reference officer_roles)
        3. officer_roles (referencing memberships)
        4. memberships (referencing organizations)
        5. organizations

        This avoids foreign key constraint errors and ensures connected data is
        cleaned up when an organization is deleted.
        """
        db = get_db()
        try:
            # Remove announcements and events tied to the organization first
            db.execute('DELETE FROM announcements WHERE OrgID = ?', (org_id,))
            db.execute('DELETE FROM events WHERE OrgID = ?', (org_id,))

            # Remove officer roles that belong to memberships for this org
            db.execute(
                'DELETE FROM officer_roles WHERE MembershipID IN (SELECT MembershipID FROM memberships WHERE OrgID = ?)',
                (org_id,)
            )

            # Remove memberships (this will orphan nothing since officer_roles are removed)
            db.execute('DELETE FROM memberships WHERE OrgID = ?', (org_id,))

            # Finally remove the organization itself
            db.execute('DELETE FROM organizations WHERE OrgID = ?', (org_id,))
            db.commit()
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while deleting organization')
            raise AppError('DB_ERROR', 'Could not delete organization', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while deleting organization')
            raise AppError('DB_ERROR', 'Could not delete organization', original_exception=e)