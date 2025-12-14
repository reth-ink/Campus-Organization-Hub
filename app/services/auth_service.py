from ..models import User
from ..database import db
from .errors import AppError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    @staticmethod
    def register(first_name: str, last_name: str, email: str, password: str):
        if not first_name or not last_name or not email or not password:
            raise AppError(
                "FirstName, LastName, Email and Password are required",
                code='INVALID_INPUT',
                http_status=400
            )
        existing = User.query.filter_by(Email=email).first()
        if existing:
            raise AppError("User with that email already exists", code='USER_EXISTS', http_status=409)
        try:
            user = User(FirstName=first_name, LastName=last_name, Email=email)
            user.PasswordHash = generate_password_hash(password)
            db.session.add(user)
            db.session.commit()
            return user
        except SQLAlchemyError:
            db.session.rollback()
            raise AppError("Database error during registration", code='DB_ERROR', http_status=500)

    @staticmethod
    def login(email: str, password: str):
        if not email or not password:
            raise AppError("Email and Password are required", code='INVALID_INPUT', http_status=400)
        user = User.query.filter_by(Email=email).first()
        if not user or not check_password_hash(user.PasswordHash, password):
            raise AppError("Invalid email or password", code='INVALID_CREDENTIALS', http_status=401)
        return user

    @staticmethod
    def find_by_email(email: str):
        if not email:
            raise AppError("Email required", code='INVALID_INPUT', http_status=400)
        user = User.query.filter_by(Email=email).first()
        if not user:
            raise AppError("User not found", code='NOT_FOUND', http_status=404)
        return user
