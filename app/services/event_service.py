import csv
import os
from datetime import datetime
from ..database import db
from ..models import Event
from .errors import AppError
from sqlalchemy import text

DATA_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data')
EVENT_CSV = os.path.join(DATA_FOLDER, 'sample_events.csv')


class EventService:

    @staticmethod
    def create_event(org_id: int, user_id: int, name: str, description: str, event_date: str, location: str):
        try:
            # Check membership
            membership_sql = text("""
                SELECT MembershipID FROM memberships
                WHERE UserID = :user_id AND OrgID = :org_id AND Status = 'Approved'
            """)
            membership = db.session.execute(membership_sql, {"user_id": user_id, "org_id": org_id}).fetchone()
            if not membership:
                raise AppError("User is not a member of this organization", code='ACCESS_DENIED', http_status=403)

            # Check officer role
            officer_sql = text("""
                SELECT OfficerRoleID FROM officer_roles
                WHERE MembershipID = :membership_id
            """)
            officer = db.session.execute(officer_sql, {"membership_id": membership.MembershipID}).fetchone()
            if not officer:
                raise AppError("Only officers can create events", code='ACCESS_DENIED', http_status=403)

            event_dt = datetime.fromisoformat(event_date) if event_date else None
            now = datetime.utcnow()

            insert_sql = text("""
                INSERT INTO events
                (OrgID, CreatedBy, EventName, Description, EventDate, Location, created_at, updated_at)
                VALUES (:org_id, :created_by, :name, :description, :event_date, :location, :created_at, :updated_at)
            """)
            db.session.execute(insert_sql, {
                "org_id": org_id,
                "created_by": officer.OfficerRoleID,
                "name": name,
                "description": description,
                "event_date": event_dt,
                "location": location,
                "created_at": now,
                "updated_at": now
            })
            db.session.commit()

            event_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
            return db.session.execute(
                text("SELECT * FROM events WHERE EventID = :id"),
                {"id": event_id}
            ).fetchone()

        except Exception as e:
            db.session.rollback()
            raise AppError(f"Database error creating event: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def get_org_events(org_id: int):
        try:
            sql = text("""
                SELECT e.EventID, e.EventName, e.Description, e.EventDate, e.Location,
                       u.FirstName, u.LastName
                FROM events e
                JOIN officer_roles o ON e.CreatedBy = o.OfficerRoleID
                JOIN memberships m ON o.MembershipID = m.MembershipID
                JOIN users u ON m.UserID = u.UserID
                WHERE e.OrgID = :org_id
                ORDER BY e.EventDate
            """)
            rows = db.session.execute(sql, {"org_id": org_id}).fetchall()
            result = []
            for r in rows:
                result.append({
                    "EventID": r.EventID,
                    "EventName": r.EventName,
                    "Description": r.Description,
                    "EventDate": r.EventDate,
                    "Location": r.Location,
                    "CreatorName": f"{r.FirstName} {r.LastName}"
                })
            return result
        except Exception as e:
            raise AppError(f"Database error fetching events: {str(e)}", code='DB_ERROR', http_status=500)

    @staticmethod
    def event_to_dict(event):
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
        if not os.path.exists(EVENT_CSV):
            return
        try:
            with open(EVENT_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('EventID') and row['EventID'] != 'N/A':
                        exists_sql = text("SELECT 1 FROM events WHERE EventID = :id")
                        if db.session.execute(exists_sql, {"id": int(row['EventID'])}).fetchone():
                            continue

                        if row.get('CreatedBy') and row['CreatedBy'] != 'N/A':
                            officer_id = int(row['CreatedBy'])
                        else:
                            continue

                        event_dt = datetime.fromisoformat(row['EventDate']) if row.get('EventDate') else None
                        now = datetime.utcnow()
                        insert_sql = text("""
                            INSERT INTO events
                            (EventID, OrgID, CreatedBy, EventName, Description, EventDate, Location, created_at, updated_at)
                            VALUES (:EventID, :OrgID, :CreatedBy, :EventName, :Description, :EventDate, :Location, :created_at, :updated_at)
                        """)
                        db.session.execute(insert_sql, {
                            "EventID": int(row['EventID']),
                            "OrgID": int(row['OrgID']),
                            "CreatedBy": officer_id,
                            "EventName": row['EventName'],
                            "Description": row.get('EventDescription', ''),
                            "EventDate": event_dt,
                            "Location": row.get('Location', ''),
                            "created_at": now,
                            "updated_at": now
                        })
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Error importing events CSV: {str(e)}", code='CSV_ERROR', http_status=500)

    @staticmethod
    def export_to_csv():
        try:
            events = db.session.execute(text("SELECT * FROM events")).fetchall()
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
