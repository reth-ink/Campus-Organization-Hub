import csv
from flask import current_app
from ..database import get_db
from ..models.membership import Membership
from ..utils.errors import AppError

class MembershipService:

    @staticmethod
    def create_membership(user_id, organization_id, status):
        db = get_db()
        try:
            db.execute(
                'INSERT INTO memberships (UserID, OrgID, Status, DateApplied, DateApproved) VALUES (?, ?, ?, ?, ?)',
                (user_id, organization_id, status, None, None)
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
    def get_memberships_by_org(org_id):
        db = get_db()
        rows = db.execute('SELECT MembershipID, UserID, OrgID, Status, DateApplied, DateApproved FROM memberships WHERE OrgID = ?', (org_id,)).fetchall()
        return [Membership(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def update_membership_status(membership_id, status):
        db = get_db()
        try:
            # If the membership is being approved, set Status and DateApproved.
            # If the membership is being rejected, remove the membership row entirely.
            st = (status or '').lower()
            if st == 'approved':
                db.execute('UPDATE memberships SET Status = ?, DateApproved = CURRENT_TIMESTAMP WHERE MembershipID = ?', (status, membership_id))
            elif st == 'rejected':
                # delete the membership when a request is rejected
                db.execute('DELETE FROM memberships WHERE MembershipID = ?', (membership_id,))
            else:
                # other statuses (e.g., Pending) - just update status and clear DateApproved
                db.execute('UPDATE memberships SET Status = ?, DateApproved = NULL WHERE MembershipID = ?', (status, membership_id))
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not update membership status: {str(e)}')

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