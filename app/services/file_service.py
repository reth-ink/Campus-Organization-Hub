import csv
import json
from io import StringIO
from ..models import User, Organization, Membership, Event
from .errors import AppError
from ..database import db

class FileService:
    @staticmethod
    def export_table_to_csv(model_class, fields: list):
        try:
            items = model_class.query.all()
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for item in items:
                row = {}
                for k in fields:
                    val = getattr(item, k, '')
                    if hasattr(val, 'isoformat'):
                        val = val.isoformat()
                    row[k] = val
                writer.writerow(row)
            return output.getvalue()
        except Exception as e:
            raise AppError(f"Export failed: {e}", code='EXPORT_ERROR', http_status=500)

    @staticmethod
    def import_users_from_json(json_str):
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                raise AppError("JSON must be an array of users", code='INVALID_INPUT', http_status=400)
            created = []
            from sqlalchemy.exc import SQLAlchemyError
            for u in data:
                first = u.get('FirstName') or u.get('first_name')
                last = u.get('LastName') or u.get('last_name')
                email = u.get('Email') or u.get('email')
                if not first or not last or not email:
                    continue
                if User.query.filter_by(Email=email).first():
                    continue
                new_user = User(FirstName=first, LastName=last, Email=email)
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
