from flask import Blueprint, request, jsonify
from ..services.user_service import UserService
from ..utils.errors import AppError

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/', methods=['GET'])
def get_users():
    return jsonify(UserService.get_all_users())

@bp.route('/import', methods=['POST'])
def import_users():
    file_path = request.json.get('file_path')
    if not file_path:
        raise AppError('INVALID_REQUEST', 'file_path is required')
    UserService.import_users_from_csv(file_path)
    return jsonify({'message': 'Users imported successfully'})
