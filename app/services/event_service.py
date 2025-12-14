from ..models import Event, Organization, OfficerRole
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class EventService:
    @staticmethod
    def create_event(org_id: int, created_by_officer_role_id: int, event_name: str, description: str = None, event_date: datetime = None, location: str = None):
        org = Organization.query.get(org_id)
        if not org:
            raise AppError("Organization not found", code='NOT_FOUND', http_status=404)
        officer = OfficerRole.query.get(created_by_officer_role_id)
        if not officer:
            raise AppError("Officer role not found", code='NOT_FOUND', http_status=404)
        if not event_name:
            raise AppError("EventName required", code='INVALID_INPUT', http_status=400)
        try:
            event = Event(OrgID=org_id, CreatedBy=created_by_officer_role_id, EventName=event_name, Description=description, EventDate=event_date, Location=location)
            db.session.add(event)
            db.session.commit()
            return event
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error creating event", code='DB_ERROR', http_status=500)

    @staticmethod
    def upcoming_events(limit: int = 10):
        events = Event.query.order_by(Event.EventDate).limit(limit).all()
        return [e.to_dict() for e in events]
