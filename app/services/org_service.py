from ..models import Organization
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError

class OrgService:
    @staticmethod
    def create_org(name: str, description: str = None, officers=None, contact_email: str = None):
        if not name:
            raise AppError("Organization name required", code='INVALID_INPUT', http_status=400)
        if Organization.query.filter_by(name=name).first():
            raise AppError("Organization already exists", code='ORG_EXISTS', http_status=409)
        try:
            officers_csv = None
            if officers:
                if isinstance(officers, list):
                    officers_csv = ','.join(map(str, officers))
                else:
                    officers_csv = str(officers)
            org = Organization(name=name, description=description, officers=officers_csv, contact_email=contact_email)
            db.session.add(org)
            db.session.commit()
            return org
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error creating organization", code='DB_ERROR', http_status=500)

    @staticmethod
    def search_orgs(query: str = None, filter_fn=None):
        """
        Demonstrates lambda usage: filter_fn is a function to apply to the list of org dicts.
        """
        orgs = Organization.query.all()
        org_dicts = list(map(lambda o: o.to_dict(), orgs))  # lambda used for transformation
        # built-in filter via lambda if provided
        if filter_fn:
            try:
                org_dicts = list(filter(filter_fn, org_dicts))
            except Exception as e:
                raise AppError(f"Filter function raised error: {e}", code='FILTER_ERROR', http_status=400)
        # simple text search using lambda
        if query:
            q = query.lower()
            org_dicts = list(filter(lambda d: q in (d.get('name') or '').lower() or q in (d.get('description') or '').lower(), org_dicts))
        return org_dicts

    @staticmethod
    def get_org(org_id):
        org = Organization.query.get(org_id)
        if not org:
            raise AppError("Organization not found", code='NOT_FOUND', http_status=404)
        return org