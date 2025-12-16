from flask import Blueprint, request, jsonify
from ..services.event_service import EventService
from ..utils.errors import AppError

bp = Blueprint('events', __name__, url_prefix='/events')

@bp.route('/', methods=['GET'])
def get_events():
    return jsonify(EventService.get_all_events())

@bp.route('/import', methods=['POST'])
def import_events():
    file_path = request.json.get('file_path')
    if not file_path:
        raise AppError('INVALID_REQUEST', 'file_path is required')
    EventService.import_events_from_csv(file_path)
    return jsonify({'message': 'Events imported successfully'})