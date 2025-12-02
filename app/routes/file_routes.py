from flask import Blueprint, request, Response, jsonify
from ..services.file_service import FileService
from ..models import User, Organization, Application, Event
from ..services.errors import AppError

file_bp = Blueprint('files', __name__)

@file_bp.route('/export/<string:table>', methods=['GET'])
def export_table(table):
    try:
        if table == 'users':
            csv_data = FileService.export_table_to_csv(User, ['id', 'username', 'role', 'full_name', 'created_at'])
        elif table == 'organizations':
            csv_data = FileService.export_table_to_csv(Organization, ['id', 'name', 'description', 'officers', 'contact_email', 'created_at'])
        elif table == 'applications':
            csv_data = FileService.export_table_to_csv(Application, ['id', 'applicant_id', 'org_id', 'status', 'submitted_at'])
        elif table == 'events':
            csv_data = FileService.export_table_to_csv(Event, ['id', 'org_id', 'title', 'location', 'start_time', 'end_time'])
        else:
            raise AppError("Unknown table", code='INVALID_INPUT', http_status=400)
        return Response(csv_data, mimetype='text/csv', headers={"Content-disposition":"attachment; filename=" + f"{table}.csv"})
    except AppError as e:
        raise e

@file_bp.route('/import/users', methods=['POST'])
def import_users():
    try:
        payload = request.get_data(as_text=True)
        created = FileService.import_users_from_json(payload)
        return jsonify({'created': created}), 201
    except AppError as e:
        raise e
