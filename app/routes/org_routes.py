from flask import Blueprint, request, jsonify
from ..services.org_service import OrgService
from ..services.errors import AppError

org_bp = Blueprint('orgs', __name__)

@org_bp.route('/', methods=['POST'])
def create_org():
    data = request.get_json() or {}
    try:
        org = OrgService.create_org(
            name=data.get('name'),
            description=data.get('description'),
            officers=data.get('officers'),
            contact_email=data.get('contact_email')
        )
        return jsonify(org.to_dict()), 201
    except AppError as e:
        raise e

@org_bp.route('/', methods=['GET'])
def list_orgs():
    q = request.args.get('q')
    try:
        # example of passing a lambda filter that filters orgs with at least one officer
        filter_fn = None
        if request.args.get('has_officers') == '1':
            filter_fn = lambda d: len(d.get('officers', [])) > 0
        orgs = OrgService.search_orgs(query=q, filter_fn=filter_fn)
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
