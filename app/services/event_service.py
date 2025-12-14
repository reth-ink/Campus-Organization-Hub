import csv
from datetime import datetime
from ..models import Event, OfficerRole, Membership, User
from ..database import db
from .errors import AppError
import os
from sqlalchemy.exc import SQLAlchemyError

DATA_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data')
EVENT_CSV = os.path.join(DATA_FOLDER, 'sample_events.csv')  # updated path

class EventService:

    @staticmethod
    def create_event(org_id: int, user_id: int, name: str, description: str, event_date: str, location: str):
        try:
            membership = Membership.query.filter_by(UserID=user_id, OrgID=org_id, Status='Approved').first()
            if not membership:
                raise AppError("User is not a member of this organization", code='ACCESS_DENIED', http_status=403)

            officer = OfficerRole.query.filter_by(MembershipID=membership.MembershipID).first()
            if not officer:
                raise AppError("Only officers can create events", code='ACCESS_DENIED', http_status=403)

            event_dt = datetime.fromisoformat(event_date) if event_date else None

            event = Event(
                OrgID=org_id,
                CreatedBy=officer.OfficerRoleID,
                EventName=name,
                Description=description,
                EventDate=event_dt,
                Location=location
            )
            db.session.add(event)
            db.session.commit()
            return event

        except SQLAlchemyError as e:
            db.session.rollback()
            raise AppError(f"Database error creating event: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def get_org_events(org_id: int):
        try:
            events = Event.query.filter_by(OrgID=org_id).order_by(Event.EventDate).all()
            result = []
            for ev in events:
                officer = OfficerRole.query.get(ev.CreatedBy)
                user = User.query.get(officer.Membership.UserID) if officer else None
                result.append({
                    "EventID": ev.EventID,
                    "EventName": ev.EventName,
                    "Description": ev.Description,
                    "EventDate": ev.EventDate,
                    "Location": ev.Location,
                    "CreatorName": f"{user.FirstName} {user.LastName}" if user else "Unknown"
                })
            return result
        except SQLAlchemyError as e:
            raise AppError(f"Database error fetching events: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def event_to_dict(event: Event):
        return {
            "id": event.EventID,
            "org_id": event.OrgID,
            "created_by": event.CreatedBy,
            "name": event.EventName,
            "description": event.Description,
            "event_date": event.EventDate.isoformat() if event.EventDate else None,
            "location": event.Location
        }

    # ---------------- CSV IMPORT / EXPORT ----------------
    @staticmethod
    def import_from_csv():
        """Import events from CSV into the database."""
        if not os.path.exists(EVENT_CSV):
            return
        try:
            with open(EVENT_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('EventID') and row['EventID'] != 'N/A':
                        event = Event.query.filter_by(EventID=int(row['EventID'])).first()
                        if event:
                            continue
                        if row.get('CreatedBy') and row['CreatedBy'] != 'N/A':
                            officer_id = int(row['CreatedBy'])
                        else:
                            continue

                        event_dt = datetime.fromisoformat(row['EventDate']) if row.get('EventDate') else None
                        event = Event(
                            EventID=int(row['EventID']),
                            OrgID=int(row['OrgID']),
                            CreatedBy=officer_id,
                            EventName=row['EventName'],
                            Description=row['EventDescription'],
                            EventDate=event_dt,
                            Location=row['Location']
                        )
                        db.session.add(event)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing events CSV: {str(e)}", code='CSV_ERROR', http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            events = Event.query.all()
            with open(EVENT_CSV, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['EventID', 'OrgID', 'CreatedBy', 'EventName', 'EventDescription', 'EventDate', 'Location']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for ev in events:
                    writer.writerow({
                        'EventID': ev.EventID,
                        'OrgID': ev.OrgID,
                        'CreatedBy': ev.CreatedBy,
                        'EventName': ev.EventName,
                        'EventDescription': ev.Description,
                        'EventDate': ev.EventDate.isoformat() if ev.EventDate else '',
                        'Location': ev.Location
                    })
        except Exception as e:
            raise AppError(f"Error exporting events CSV: {str(e)}", code='CSV_ERROR', http_status=500)
