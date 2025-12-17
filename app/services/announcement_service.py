import csv
import json
import sqlite3
from flask import current_app
from ..database import get_db
from ..models.announcement import Announcement
from ..utils.errors import AppError

class AnnouncementService:

    @staticmethod
    def create_announcement(org_id, created_by, title, content, date_posted, attachments=None):
        db = get_db()
        try:
            att_val = None
            if attachments:
                try:
                    att_val = json.dumps(attachments)
                except (TypeError, ValueError) as e:
                    current_app.logger.debug('Invalid attachments value; storing as NULL: %s', e)
                    att_val = None

            # If date_posted is None, omit the DatePosted column so the
            # database DEFAULT (CURRENT_TIMESTAMP) is applied. Inserting
            # a NULL value would override the default and leave DatePosted empty.
            if date_posted is None:
                db.execute(
                    'INSERT INTO announcements (OrgID, CreatedBy, Title, Content, Attachments) VALUES (?, ?, ?, ?, ?)',
                    (org_id, created_by, title, content, att_val)
                )
            else:
                db.execute(
                    'INSERT INTO announcements (OrgID, CreatedBy, Title, Content, DatePosted, Attachments) VALUES (?, ?, ?, ?, ?, ?)',
                    (org_id, created_by, title, content, date_posted, att_val)
                )
            db.commit()
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while creating announcement')
            raise AppError('DB_ERROR', 'Could not create announcement', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while creating announcement')
            raise AppError('DB_ERROR', 'Could not create announcement', original_exception=e)

    @staticmethod
    def get_all_announcements():
        db = get_db()
        # select only the announcement fields used by the model (exclude audit columns)
        rows = db.execute('SELECT AnnouncementID, OrgID, CreatedBy, Title, Content, DatePosted, Attachments FROM announcements').fetchall()
        import json
        out = []
        for row in rows:
            d = dict(row)
            # parse Attachments JSON if present
            att = d.get('Attachments')
            if att and isinstance(att, str):
                try:
                    d['Attachments'] = json.loads(att)
                except json.JSONDecodeError as e:
                    current_app.logger.debug('Failed to parse attachments JSON: %s', e)
                    d['Attachments'] = None
                except Exception:
                    d['Attachments'] = None
            out.append(Announcement(**d).to_dict())
        return out

    @staticmethod
    def import_announcements_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for a in reader:
                    org = a.get('OrgID') or a.get('org_id')
                    created_by = a.get('CreatedBy') or a.get('created_by')
                    title = a.get('Title') or a.get('title')
                    content = a.get('Content') or a.get('content')
                    date_posted = a.get('DatePosted') or a.get('date_posted')
                    try:
                        AnnouncementService.create_announcement(org, created_by, title, content, date_posted)
                    except AppError:
                        current_app.logger.exception('Failed to create announcement from CSV row, continuing')
                        continue
        except (csv.Error, OSError) as e:
            current_app.logger.exception('Error reading announcements CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error importing announcements from CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)