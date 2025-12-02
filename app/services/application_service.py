from ..models import Application, User, Organization
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError

class ApplicationService:
    @staticmethod
    def submit_application(applicant_id: int, org_id: int, statement: str = None):
        # validations
        applicant = User.query.get(applicant_id)
        if not applicant:
            raise AppError("Applicant not found", code='NOT_FOUND', http_status=404)
        org = Organization.query.get(org_id)
        if not org:
            raise AppError("Organization not found", code='NOT_FOUND', http_status=404)
        try:
            existing = Application.query.filter_by(applicant_id=applicant_id, org_id=org_id).first()
            if existing:
                raise AppError("Application already submitted", code='ALREADY_SUBMITTED', http_status=409)
            application = Application(applicant_id=applicant_id, org_id=org_id, statement=statement)
            db.session.add(application)
            db.session.commit()
            return application
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error submitting application", code='DB_ERROR', http_status=500)

    @staticmethod
    def list_applications(org_id: int = None, status: str = None, process_fn=None):
        qs = Application.query
        if org_id:
            qs = qs.filter_by(org_id=org_id)
        if status:
            qs = qs.filter_by(status=status)
        apps = qs.all()
        app_dicts = list(map(lambda a: a.to_dict(), apps))

        # demonstrate lambda processing: allow caller to pass processing function (e.g., map or filter)
        if process_fn:
            try:
                app_dicts = process_fn(app_dicts)
            except Exception as e:
                raise AppError(f"Processing function failed: {e}", code='PROCESS_ERROR', http_status=400)
        return app_dicts

    @staticmethod
    def update_status(application_id: int, new_status: str):
        if new_status not in ('pending', 'accepted', 'rejected'):
            raise AppError("Invalid status", code='INVALID_INPUT', http_status=400)
        app = Application.query.get(application_id)
        if not app:
            raise AppError("Application not found", code='NOT_FOUND', http_status=404)
        try:
            app.status = new_status
            db.session.commit()
            return app
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error updating status", code='DB_ERROR', http_status=500)