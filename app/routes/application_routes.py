from flask import Blueprint, request, jsonify
from ..services.application_service import ApplicationService
from ..services.errors import AppError

app_bp = Blueprint('applications', __name__)

@app_bp.route('/', methods=['POST'])
def submit_application():
    data = request.get_json() or {}
    try:
        application = ApplicationService.submit_application(
            applicant_id=data.get('applicant_id'),
            org_id=data.get('org_id'),
            statement=data.get('statement')
        )
        return jsonify(application.to_dict()), 201
    except AppError as e:
        raise e

@app_bp.route('/', methods=['GET'])
def list_applications():
    org_id = request.args.get('org_id', type=int)
    status = request.args.get('status')
    try:
        # Example: pass a lambda to process the result -> return only most recent 10 applications
        process_fn = lambda arr: sorted(arr, key=lambda x: x['submitted_at'], reverse=True)[:10]
        apps = ApplicationService.list_applications(org_id=org_id, status=status, process_fn=process_fn)
        return jsonify({'applications': apps})
    except AppError as e:
        raise e

@app_bp.route('/<int:app_id>/status', methods=['PATCH'])
def update_status(app_id):
    data = request.get_json() or {}
    try:
        app = ApplicationService.update_status(application_id=app_id, new_status=data.get('status'))
        return jsonify(app.to_dict())
    except AppError as e:
        raise e
