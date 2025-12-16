import csv
from flask import current_app
from ..database import get_db
from ..models.event import Event
from ..utils.errors import AppError

class EventService:
    
    @staticmethod
    def create_event(event_name, event_description, event_date, org_id, created_by=None, location=None):
        db = get_db()
        try:
            db.execute(
                'INSERT INTO events (OrgID, CreatedBy, EventName, Description, EventDate, Location) VALUES (?, ?, ?, ?, ?, ?)',
                (org_id, created_by, event_name, event_description, event_date, location)
            )
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create event: {str(e)}')

    @staticmethod
    def get_all_events():
        db = get_db()
        # map DB columns to Event model parameters (alias Description -> EventDescription)
        rows = db.execute('SELECT EventID, OrgID, CreatedBy, EventName, Description AS EventDescription, EventDate, Location FROM events').fetchall()
        return [Event(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def import_events_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for e in reader:
                    # support PascalCase CSV headers from data/ (EventName, EventDescription, EventDate, OrgID)
                    name = e.get('EventName') or e.get('title') or e.get('name')
                    desc = e.get('EventDescription') or e.get('description')
                    date = e.get('EventDate') or e.get('date')
                    org = e.get('OrgID') or e.get('organization_id') or e.get('org_id')
                    created_by = e.get('CreatedBy')
                    location = e.get('Location')
                    EventService.create_event(name, desc, date, org, created_by, location)
        except Exception as e:
            raise AppError('CSV_IMPORT_ERROR', f'Error importing CSV: {str(e)}')