import csv
import os
from flask import current_app
from ..database import get_db
from ..models.user import User
from ..utils.errors import AppError
from passlib.hash import pbkdf2_sha256

class UserService:

    @staticmethod
    def create_user(first_name, last_name, email, password=None):
        db = get_db()
        try:
            # Determine password hash to store. If a password was provided and
            # looks like a bcrypt hash (starts with $2), assume it's already
            # hashed. Otherwise hash the plaintext. If no password provided,
            # use a default from environment or fallback to a safe default.
            if not password:
                default_pw = os.environ.get('SEED_DEFAULT_PASSWORD', 'ChangeMe123!')
                hashed = pbkdf2_sha256.hash(default_pw)
            else:
                p = str(password)
                # If the value already looks like a passlib pbkdf2_sha256 hash,
                # store it as-is. Otherwise hash the provided plaintext.
                if p.startswith('$pbkdf2-sha256$'):
                    hashed = p
                else:
                    hashed = pbkdf2_sha256.hash(p)

            db.execute(
                'INSERT OR IGNORE INTO users (FirstName, LastName, Email, PasswordHash) VALUES (?, ?, ?, ?)',
                (first_name, last_name, email, hashed)
            )
            db.commit()
        except Exception as e:
            raise AppError('DB_ERROR', f'Could not create user: {str(e)}')

    @staticmethod
    def get_all_users():
        db = get_db()
        # select only public fields so model construction doesn't receive audit columns
        rows = db.execute('SELECT UserID, FirstName, LastName, Email FROM users').fetchall()
        return [User(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def get_user_row_by_email(email):
        """Return the raw DB row (as a dict) for the given email, including PasswordHash.
        Returns None if not found.
        """
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE Email = ?', (email,)).fetchone()
        return dict(row) if row is not None else None

    @staticmethod
    def get_user_row_by_id(user_id):
        db = get_db()
        row = db.execute('SELECT UserID, FirstName, LastName, Email, created_at FROM users WHERE UserID = ?', (user_id,)).fetchone()
        return dict(row) if row is not None else None

    @staticmethod
    def verify_password(plain_password, password_hash):
        try:
            return pbkdf2_sha256.verify(str(plain_password), password_hash)
        except Exception:
            return False

    @staticmethod
    def import_users_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for u in reader:
                    first = u.get('FirstName') or u.get('first_name')
                    last = u.get('LastName') or u.get('last_name')
                    email = u.get('Email') or u.get('email')
                    # CSV may include a pre-hashed PasswordHash or a plaintext 'password'
                    password = u.get('PasswordHash') or u.get('password') or None
                    UserService.create_user(first, last, email, password)
        except Exception as e:
            raise AppError('CSV_IMPORT_ERROR', f'Error importing CSV: {str(e)}')
