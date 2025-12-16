from flask import Blueprint, request, jsonify
from ..services.organization_service import OrgService
from ..utils.errors import AppError

bp = Blueprint('organizations', __name__, url_prefix='/organizations')

@bp.route('/', methods=['GET'])
def get_organizations():
    return jsonify(OrgService.get_all_organizations())

@bp.route('/import', methods=['POST'])
def import_organizations():
    file_path = request.json.get('file_path')
    if not file_path:
        raise AppError('INVALID_REQUEST', 'file_path is required')
    OrgService.import_organizations_from_csv(file_path)
    return jsonify({'message': 'Organizations imported successfully'})