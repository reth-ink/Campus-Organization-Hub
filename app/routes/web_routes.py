from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..services.org_service import OrgService
from ..services.event_service import EventService
from ..services.auth_service import AuthService
from ..services.errors import AppError

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def home():
    try:
        orgs = OrgService.search_orgs()
        events = EventService.upcoming_events(limit=5)
    except AppError:
        orgs, events = [], []
    return render_template('home.html', orgs=orgs, events=events)

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        try:
            AuthService.register(first_name=data.get('first_name'), last_name=data.get('last_name'), email=data.get('email'))
            return redirect(url_for('web.login'))
        except AppError as e:
            return render_template('register.html', error=e.message)
    return render_template('register.html')

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        try:
            # simple lookup — no passwords in schema
            user = AuthService.find_by_email(email)
            # in real app we'd set session / cookie; keeping simple
            return redirect(url_for('web.home'))
        except AppError as e:
            return render_template('login.html', error=e.message)
    return render_template('login.html')

@web_bp.route('/org/<int:org_id>')
def org_detail(org_id):
    try:
        org = OrgService.get_org(org_id)
        org = org.to_dict()
    except AppError:
        return redirect(url_for('web.home'))
    return render_template('org_detail.html', org=org)

@web_bp.route('/event/<int:event_id>')
def event_detail(event_id):
    # fetch event from DB
    try:
        events = EventService.upcoming_events(limit=100)
        event = next((e for e in events if e['EventID'] == event_id), None)
        if not event:
            return redirect(url_for('web.home'))
    except AppError:
        return redirect(url_for('web.home'))
    return render_template('event_detail.html', event=event)
