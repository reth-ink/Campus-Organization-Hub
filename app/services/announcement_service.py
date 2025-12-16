import csv
from flask import current_app
from ..database import get_db
from ..models.announcement import Announcement
from ..utils.errors import AppError

class AnnouncementService:

    @staticmethod
    def create_announcement(org_id, created_by, title, content, date_posted):
        db = get_db()
        try:
            db.execute(
                'INSERT INTO announcements (OrgID, CreatedBy, Title, Content, DatePosted) VALUES (?, ?, ?, ?, ?)',
                (org_id, created_by, title, content, date_posted)
            )
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create announcement: {str(e)}')

    @staticmethod
    def get_all_announcements():
        db = get_db()
        # select only the announcement fields used by the model (exclude audit columns)
        rows = db.execute('SELECT AnnouncementID, OrgID, CreatedBy, Title, Content, DatePosted FROM announcements').fetchall()
        return [Announcement(**dict(row)).to_dict() for row in rows]

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