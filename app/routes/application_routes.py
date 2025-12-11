from flask import Blueprint, request, jsonify
from ..services.application_service import ApplicationService
from ..services.errors import AppError

app_bp = Blueprint('applications', __name__)

@app_bp.route('/', methods=['POST'])
def submit_application():
    data = request.get_json() or {}
    try:
        membership = ApplicationService.submit_application(
            user_id=data.get('user_id'),
            org_id=data.get('org_id')
        )
        return jsonify(membership.to_dict()), 201
    except AppError as e:
        raise e

@app_bp.route('/', methods=['GET'])
def list_applications():
    org_id = request.args.get('org_id', type=int)
    status = request.args.get('status')
    try:
        apps = ApplicationService.list_applications(org_id=org_id, status=status)
        return jsonify({'applications': apps})
    except AppError as e:
        raise e

@app_bp.route('/<int:membership_id>/status', methods=['PATCH'])
def update_status(membership_id):
    data = request.get_json() or {}
    try:
        membership = ApplicationService.update_status(membership_id=membership_id, new_status=data.get('status'))
        return jsonify(membership.to_dict())
    except AppError as e:
        raise e
