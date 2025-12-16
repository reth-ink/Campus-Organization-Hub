from flask import Blueprint, request, jsonify
from ..services.officer_role_service import OfficerRoleService
from ..utils.errors import AppError

bp = Blueprint('officer_roles', __name__, url_prefix='/officer_roles')

@bp.route('/', methods=['GET'])
def get_officer_roles():
    return jsonify(OfficerRoleService.get_all_officer_roles())

@bp.route('/import', methods=['POST'])
def import_officer_roles():
    file_path = request.json.get('file_path')
    if not file_path:
        raise AppError('INVALID_REQUEST', 'file_path is required')
    OfficerRoleService.import_officer_roles_from_csv(file_path)
    return jsonify({'message': 'Officer roles imported successfully'})
