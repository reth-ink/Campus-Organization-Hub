from ..models import Organization
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError

class OrgService:
    @staticmethod
    def create_org(org_name: str, description: str = None):
        if not org_name:
            raise AppError("Organization name required", code='INVALID_INPUT', http_status=400)
        if Organization.query.filter_by(OrgName=org_name).first():
            raise AppError("Organization already exists", code='ORG_EXISTS', http_status=409)
        try:
            org = Organization(OrgName=org_name, Description=description)
            db.session.add(org)
            db.session.commit()
            return org
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error creating organization", code='DB_ERROR', http_status=500)

    @staticmethod
    def search_orgs(query: str = None):
        orgs = Organization.query.all()
        org_dicts = list(map(lambda o: o.to_dict(), orgs))
        if query:
            q = query.lower()
            org_dicts = list(filter(lambda d: q in (d.get('OrgName') or '').lower() or q in (d.get('Description') or '').lower(), org_dicts))
        return org_dicts

    @staticmethod
    def get_org(org_id):
        org = Organization.query.get(org_id)
        if not org:
            raise AppError("Organization not found", code='NOT_FOUND', http_status=404)
        return org
