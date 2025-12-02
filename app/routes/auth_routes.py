from flask import Blueprint, request, jsonify
from ..services.auth_service import AuthService
from ..services.errors import AppError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    try:
        user = AuthService.register(
            username=data.get('username'),
            password=data.get('password'),
            full_name=data.get('full_name'),
            role=data.get('role', 'student')
        )
        return jsonify(user.to_dict()), 201
    except AppError as e:
        raise e

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    try:
        user = AuthService.authenticate(username=data.get('username'), password=data.get('password'))
        # NOTE: return minimal user info; token-based auth should be added
        return jsonify({'message': 'Authenticated', 'user': user.to_dict()})
    except AppError as e:
        raise e