from flask import Blueprint, request, jsonify
from ..services.event_service import EventService
from ..services.errors import AppError
from dateutil import parser

event_bp = Blueprint('events', __name__)

@event_bp.route('/', methods=['POST'])
def create_event():
    data = request.get_json() or {}
    try:
        start = parser.isoparse(data['start_time']) if data.get('start_time') else None
        end = parser.isoparse(data['end_time']) if data.get('end_time') else None
        event = EventService.create_event(
            org_id=data.get('org_id'),
            title=data.get('title'),
            description=data.get('description'),
            location=data.get('location'),
            start_time=start,
            end_time=end
        )
        return jsonify(event.to_dict()), 201
    except AppError as e:
        raise e
    except Exception as e:
        # parser errors etc
        raise AppError(f"Invalid input: {e}", code='INVALID_INPUT', http_status=400)

@event_bp.route('/upcoming', methods=['GET'])
def upcoming():
    try:
        events = EventService.upcoming_events(limit=int(request.args.get('limit', 10)))
        return jsonify({'events': events})
    except AppError as e:
        raise e
