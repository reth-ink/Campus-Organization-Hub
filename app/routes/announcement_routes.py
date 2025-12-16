from flask import Blueprint, request, jsonify
from ..services.announcement_service import AnnouncementService
from ..utils.errors import AppError

bp = Blueprint('announcements', __name__, url_prefix='/announcements')

@bp.route('/', methods=['GET'])
def get_announcements():
    return jsonify(AnnouncementService.get_all_announcements())

@bp.route('/import', methods=['POST'])
def import_announcements():
    file_path = request.json.get('file_path')
    if not file_path:
        raise AppError('INVALID_REQUEST', 'file_path is required')
    AnnouncementService.import_announcements_from_csv(file_path)
    return jsonify({'message': 'Announcements imported successfully'})