from flask import Blueprint, request, jsonify
from ..services.event_service import EventService
from ..services.errors import AppError
from dateutil import parser

event_bp = Blueprint('events', __name__)

@event_bp.route('/', methods=['POST'])
def create_event():
    data = request.get_json() or {}
    try:
        event_date = parser.isoparse(data['event_date']) if data.get('event_date') else None
        event = EventService.create_event(
            org_id=data.get('org_id'),
            created_by_officer_role_id=data.get('created_by'),
            event_name=data.get('event_name'),
            description=data.get('description'),
            event_date=event_date,
            location=data.get('location')
        )
        return jsonify(event.to_dict()), 201
    except AppError as e:
        raise e
    except Exception as e:
        raise AppError(f"Invalid input: {e}", code='INVALID_INPUT', http_status=400)

@event_bp.route('/upcoming', methods=['GET'])
def upcoming():
    try:
        events = EventService.upcoming_events(limit=int(request.args.get('limit', 10)))
        return jsonify({'events': events})
    except AppError as e:
        raise e
