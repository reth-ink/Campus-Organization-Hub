import csv
import json
from io import StringIO
from ..models import User, Organization, Application, Event
from .errors import AppError
from ..database import db

class FileService:
    @staticmethod
    def export_table_to_csv(model_class, fields: list):
        """
        Generic CSV exporter for a SQLAlchemy model.
        Returns CSV string.
        """
        try:
            items = model_class.query.all()
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for item in items:
                row = {k: getattr(item, k, '') for k in fields}
                writer.writerow(row)
            return output.getvalue()
        except Exception as e:
            raise AppError(f"Export failed: {e}", code='EXPORT_ERROR', http_status=500)

    @staticmethod
    def import_users_from_json(json_str):
        """
        Expecting an array of objects: [{"username":"...","password":"...","full_name":"...","role":"..."}]
        Uses lambda internally for quick validation transformation.
        """
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                raise AppError("JSON must be an array of users", code='INVALID_INPUT', http_status=400)
            # transform and validate using lambda
            transform = lambda u: {
                'username': u.get('username'),
                'password': u.get('password'),
                'full_name': u.get('full_name'),
                'role': u.get('role', 'student')
            }
            users = list(map(transform, data))
            created = []
            from sqlalchemy.exc import SQLAlchemyError
            for u in users:
                if not u['username'] or not u['password']:
                    continue
                # skip existing
                if User.query.filter_by(username=u['username']).first():
                    continue
                new_user = User(username=u['username'], full_name=u['full_name'], role=u['role'])
                new_user.set_password(u['password'])
                db.session.add(new_user)
                created.append(new_user)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                raise
            return [c.to_dict() for c in created]
        except AppError:
            raise
        except Exception as e:
            raise AppError(f"Import failed: {e}", code='IMPORT_ERROR', http_status=500)