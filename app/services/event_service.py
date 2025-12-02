from ..models import Event, Organization
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class EventService:
    @staticmethod
    def create_event(org_id: int, title: str, description: str = None, location: str = None, start_time: datetime = None, end_time: datetime = None):
        org = Organization.query.get(org_id)
        if not org:
            raise AppError("Organization not found", code='NOT_FOUND', http_status=404)
        if not title:
            raise AppError("Title required", code='INVALID_INPUT', http_status=400)
        try:
            event = Event(org_id=org_id, title=title, description=description, location=location, start_time=start_time, end_time=end_time)
            db.session.add(event)
            db.session.commit()
            return event
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error creating event", code='DB_ERROR', http_status=500)

    @staticmethod
    def upcoming_events(limit: int = 10):
        # Return upcoming events sorted by start_time using lambda in sort key
        events = Event.query.filter(Event.start_time != None).order_by(Event.start_time).limit(limit).all()
        # transform
        event_dicts = list(map(lambda e: e.to_dict(), events))
        return event_dicts