from ..models import User
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError

class AuthService:
    @staticmethod
    def register(username: str, password: str, full_name: str = None, role='student'):
        if not username or not password:
            raise AppError("Username and password required", code='INVALID_INPUT', http_status=400)
        existing = User.query.filter_by(username=username).first()
        if existing:
            raise AppError("User already exists", code='USER_EXISTS', http_status=409)
        try:
            user = User(username=username, full_name=full_name, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user
        except SQLAlchemyError as e:
            db.session.rollback()
            raise AppError("Database error during registration", code='DB_ERROR', http_status=500)

    @staticmethod
    def authenticate(username: str, password: str):
        if not username:
            raise AppError("Username required", code='INVALID_INPUT', http_status=400)
        user = User.query.filter_by(username=username).first()
        if not user or not user.verify_password(password):
            raise AppError("Invalid username or password", code='AUTH_FAILED', http_status=401)
        # For simplicity, return user object. Tokenization/JWT can be added.
        return user
