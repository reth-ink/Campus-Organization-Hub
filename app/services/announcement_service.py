import csv
from flask import current_app
from ..database import get_db
from ..models.announcement import Announcement
from ..utils.errors import AppError

class AnnouncementService:

    @staticmethod
    def create_announcement(org_id, created_by, title, content, date_posted, attachments=None):
        db = get_db()
        try:
            import json
            att_val = None
            if attachments:
                try:
                    att_val = json.dumps(attachments)
                except Exception:
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
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create announcement: {str(e)}')

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
                    AnnouncementService.create_announcement(org, created_by, title, content, date_posted)
        except Exception as e:
            raise AppError('CSV_IMPORT_ERROR', f'Error importing CSV: {str(e)}')