"""Event service: CRUD and import helpers for events.

This module provides a thin service layer between routes and the sqlite3
database. Error handling is explicit: failures are logged and translated to
AppError with the original exception attached for easier debugging.
"""

import csv
import sqlite3
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
        except sqlite3.DatabaseError as e:
            # Log and convert to AppError with the original exception attached
            current_app.logger.exception('Database error while creating event')
            raise AppError('DB_ERROR', 'Could not create event', original_exception=e)
        except Exception as e:
            # Fallback for unexpected errors
            current_app.logger.exception('Unexpected error while creating event')
            raise AppError('DB_ERROR', 'Could not create event', original_exception=e)

    @staticmethod
    def get_all_events():
        db = get_db()
        # map DB columns to Event model parameters (alias Description -> EventDescription)
        rows = db.execute('SELECT EventID, OrgID, CreatedBy, EventName, Description AS EventDescription, EventDate, Location FROM events').fetchall()
        events = [Event(**dict(row)).to_dict() for row in rows]
        # demonstrate lambda usage: sort events by EventDate (fallback to EventName)
        try:
            events_sorted = sorted(
                events,
                key=lambda e: (e.get('EventDate') or e.get('EventName') or '')
            )
            return events_sorted
        except (TypeError, AttributeError, KeyError) as e:
            # If event structures are unexpected, log and return unsorted list
            current_app.logger.exception('Failed to sort events; returning unsorted list')
            return events
        except Exception as e:
            current_app.logger.exception('Unexpected error while retrieving events')
            return events

    @staticmethod
    def import_events_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # support PascalCase CSV headers from data/ (EventName, EventDescription, EventDate, OrgID)
                    name = row.get('EventName') or row.get('title') or row.get('name')
                    desc = row.get('EventDescription') or row.get('description')
                    date = row.get('EventDate') or row.get('date')
                    org = row.get('OrgID') or row.get('organization_id') or row.get('org_id')
                    created_by = row.get('CreatedBy') or row.get('created_by')
                    location = row.get('Location') or row.get('location')

                    # Basic validation: ensure required fields exist
                    if not name or not date or not org:
                        current_app.logger.debug('Skipping CSV row due to missing required fields: %s', row)
                        continue

                    try:
                        EventService.create_event(name, desc, date, org, created_by, location)
                    except AppError as ae:
                        # Log and continue importing other rows
                        current_app.logger.exception('Failed to create event from CSV row')
                        continue
        except (csv.Error, OSError) as e:
            current_app.logger.exception('Error reading events CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error importing events from CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)