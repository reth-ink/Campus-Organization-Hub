import csv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from ..database import db
from .errors import AppError
from ..models import User

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
USERS_CSV = os.path.join(DATA_FOLDER, 'users.csv')

class UserService:

    @staticmethod
    def import_from_csv():
        if not os.path.exists(USERS_CSV):
            return

        try:
            with open(USERS_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get('UserID') or not row.get('Email'):
                        continue

                    exists = db.session.execute(
                        db.select(User).filter_by(UserID=int(row['UserID']))
                    ).scalar()
                    if exists:
                        continue

                    user = User(
                        UserID=int(row['UserID']),
                        FirstName=row.get('FirstName', ''),
                        LastName=row.get('LastName', ''),
                        Email=row.get('Email', ''),
                        PasswordHash=generate_password_hash("default123"),  # default password
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(user)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise AppError(
                f"Error importing users CSV: {str(e)}",
                code="CSV_ERROR",
                http_status=500
            )
