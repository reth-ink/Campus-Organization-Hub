from flask import Blueprint, request, jsonify
from ..services.org_service import OrgService
from ..services.errors import AppError

org_bp = Blueprint('orgs', __name__)

@org_bp.route('/', methods=['POST'])
def create_org():
    data = request.get_json() or {}
    try:
        org = OrgService.create_org(
            org_name=data.get('org_name') or data.get('OrgName'),
            description=data.get('description') or data.get('Description')
        )
        return jsonify(org.to_dict()), 201
    except AppError as e:
        raise e

@org_bp.route('/', methods=['GET'])
def list_orgs():
    q = request.args.get('q')
    try:
        orgs = OrgService.search_orgs(query=q)
        return jsonify({'results': orgs})
    except AppError as e:
        raise e

@org_bp.route('/<int:org_id>', methods=['GET'])
def get_org(org_id):
    try:
        org = OrgService.get_org(org_id)
        return jsonify(org.to_dict())
    except AppError as e:
        raise e
