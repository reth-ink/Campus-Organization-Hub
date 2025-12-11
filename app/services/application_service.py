from ..models import Membership, User, Organization
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class ApplicationService:
    @staticmethod
    def submit_application(user_id: int, org_id: int):
        user = User.query.get(user_id)
        if not user:
            raise AppError("User not found", code='NOT_FOUND', http_status=404)
        org = Organization.query.get(org_id)
        if not org:
            raise AppError("Organization not found", code='NOT_FOUND', http_status=404)
        try:
            existing = Membership.query.filter_by(UserID=user_id, OrgID=org_id).first()
            if existing:
                raise AppError("Application already exists", code='ALREADY_SUBMITTED', http_status=409)
            membership = Membership(UserID=user_id, OrgID=org_id, Status='Pending', DateApplied=datetime.utcnow())
            db.session.add(membership)
            db.session.commit()
            return membership
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error submitting application", code='DB_ERROR', http_status=500)

    @staticmethod
    def list_applications(org_id: int = None, status: str = None, limit: int = 50):
        qs = Membership.query
        if org_id:
            qs = qs.filter_by(OrgID=org_id)
        if status:
            qs = qs.filter_by(Status=status)
        memberships = qs.order_by(Membership.DateApplied.desc()).limit(limit).all()
        return [m.to_dict() for m in memberships]

    @staticmethod
    def update_status(membership_id: int, new_status: str):
        if new_status not in ('Pending', 'Approved', 'Rejected'):
            raise AppError("Invalid status", code='INVALID_INPUT', http_status=400)
        membership = Membership.query.get(membership_id)
        if not membership:
            raise AppError("Membership not found", code='NOT_FOUND', http_status=404)
        try:
            membership.Status = new_status
            if new_status == 'Approved':
                membership.DateApproved = datetime.utcnow()
            db.session.commit()
            return membership
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error updating membership", code='DB_ERROR', http_status=500)
