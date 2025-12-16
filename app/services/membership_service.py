import csv
from flask import current_app
from ..database import get_db
from ..models.membership import Membership
from ..utils.errors import AppError

class MembershipService:

    @staticmethod
    def create_membership(user_id, organization_id, role):
        db = get_db()
        try:
            db.execute(
                'INSERT INTO memberships (UserID, OrgID, Status, DateApplied, DateApproved) VALUES (?, ?, ?, ?, ?)',
                (user_id, organization_id, role, None, None)
            )
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create membership: {str(e)}')

    @staticmethod
    def get_all_memberships():
        db = get_db()
        # select only fields the Membership model expects
        rows = db.execute('SELECT MembershipID, UserID, OrgID, Status, DateApplied, DateApproved FROM memberships').fetchall()
        return [Membership(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def import_memberships_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for m in reader:
                    user = m.get('UserID') or m.get('user_id')
                    org = m.get('OrgID') or m.get('organization_id')
                    status = m.get('Status') or m.get('status')
                    # DateApplied/DateApproved are available in CSV but create_membership currently sets None
                    MembershipService.create_membership(user, org, status)
        except Exception as e:
            raise AppError('CSV_IMPORT_ERROR', f'Error importing CSV: {str(e)}')