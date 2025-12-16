from flask import Blueprint, request, jsonify
from ..services.membership_service import MembershipService
from ..utils.errors import AppError

bp = Blueprint('memberships', __name__, url_prefix='/memberships')

@bp.route('/', methods=['GET'])
def get_memberships():
    return jsonify(MembershipService.get_all_memberships())

@bp.route('/import', methods=['POST'])
def import_memberships():
    file_path = request.json.get('file_path')
    if not file_path:
        raise AppError('INVALID_REQUEST', 'file_path is required')
    MembershipService.import_memberships_from_csv(file_path)
    return jsonify({'message': 'Memberships imported successfully'})
