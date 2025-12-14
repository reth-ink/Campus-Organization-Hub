from flask import Blueprint, request, jsonify
from ..services.auth_service import AuthService
from ..services.errors import AppError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    try:
        user = AuthService.register(
            first_name=data.get('first_name') or data.get('FirstName'),
            last_name=data.get('last_name') or data.get('LastName'),
            email=data.get('email') or data.get('Email')
        )
        return jsonify(user.to_dict()), 201
    except AppError as e:
        raise e

@auth_bp.route('/lookup', methods=['GET'])
def lookup():
    # simple lookup by email - useful for the web-based login redirect
    email = request.args.get('email')
    try:
        user = AuthService.find_by_email(email)
        return jsonify(user.to_dict())
    except AppError as e:
        raise e
