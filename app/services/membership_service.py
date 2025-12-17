import csv
import sqlite3
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
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while creating membership')
            raise AppError('DB_ERROR', 'Could not create membership', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while creating membership')
            raise AppError('DB_ERROR', 'Could not create membership', original_exception=e)

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
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while updating membership status')
            raise AppError('DB_ERROR', 'Could not update membership status', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while updating membership status')
            raise AppError('DB_ERROR', 'Could not update membership status', original_exception=e)

    @staticmethod
    def import_memberships_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                # normalize rows using a small lambda mapping to demonstrate lambda usage
                transform = lambda r: (
                    r.get('UserID') or r.get('user_id'),
                    r.get('OrgID') or r.get('organization_id'),
                    r.get('Status') or r.get('status')
                )
                for user, org, status in map(transform, reader):
                    # DateApplied/DateApproved are available in CSV but create_membership currently sets None
                    try:
                        MembershipService.create_membership(user, org, status)
                    except AppError:
                        current_app.logger.exception('Failed to create membership from CSV row, continuing')
                        continue
        except (csv.Error, OSError) as e:
            current_app.logger.exception('Error reading memberships CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error importing memberships from CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)