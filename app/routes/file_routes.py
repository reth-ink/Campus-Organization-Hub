from flask import Blueprint, request, Response, jsonify
from ..services.file_service import FileService
from ..models import User, Organization, Membership, Event
from ..services.errors import AppError

file_bp = Blueprint('files', __name__)

@file_bp.route('/export/<string:table>', methods=['GET'])
def export_table(table):
    try:
        if table == 'users':
            csv_data = FileService.export_table_to_csv(User, ['UserID', 'FirstName', 'LastName', 'Email'])
        elif table == 'organizations':
            csv_data = FileService.export_table_to_csv(Organization, ['OrgID', 'OrgName', 'Description'])
        elif table == 'memberships':
            csv_data = FileService.export_table_to_csv(Membership, ['MembershipID', 'UserID', 'OrgID', 'Status', 'DateApplied', 'DateApproved'])
        elif table == 'events':
            csv_data = FileService.export_table_to_csv(Event, ['EventID', 'OrgID', 'CreatedBy', 'EventName', 'EventDate', 'Location'])
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
