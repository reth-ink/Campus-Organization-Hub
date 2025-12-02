from flask import Blueprint, render_template, request, redirect, url_for

# Commented out real services for now
# from ..services.auth_service import AuthService
# from ..services.org_service import OrgService
# from ..services.event_service import EventService
# from ..services.application_service import ApplicationService
# from ..services.errors import AppError

web_bp = Blueprint('web', __name__)

# ----------------------------------------
# Home / Dashboard
# ----------------------------------------
@web_bp.route('/')
def home():
    # Fake organizations
    orgs = [
        {"id": 1, "name": "Org 1", "description": "Description for Org 1",
         "officers": ["user1"], "contact_email": "org1@example.com", "created_at": "2025-12-01T00:00:00"},
        {"id": 2, "name": "Org 2", "description": "Description for Org 2",
         "officers": [], "contact_email": "org2@example.com", "created_at": "2025-12-01T00:00:00"},
        {"id": 3, "name": "Org 3", "description": "Description for Org 3",
         "officers": ["user2","user3"], "contact_email": "org3@example.com", "created_at": "2025-12-01T00:00:00"},
    ]

    # Fake upcoming events
    events = [
        {"id": 1, "org_id": 1, "title": "Event 1", "description": "Details for Event 1",
         "location": "Main Hall", "start_time": "2025-12-05T10:00:00",
         "end_time": "2025-12-05T12:00:00", "created_at": "2025-12-01T00:00:00"},
        {"id": 2, "org_id": 2, "title": "Event 2", "description": "Details for Event 2",
         "location": "Auditorium", "start_time": "2025-12-10T14:00:00",
         "end_time": "2025-12-10T16:00:00", "created_at": "2025-12-01T00:00:00"},
    ]

    # Real DB calls commented out
    # try:
    #     orgs = OrgService.search_orgs()
    #     events = EventService.upcoming_events(limit=5)
    # except AppError as e:
    #     orgs, events = [], []

    return render_template('home.html', orgs=orgs, events=events)

# ----------------------------------------
# Registration
# ----------------------------------------
@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Temporary: redirect to login
        return redirect(url_for('web.login'))

        # Real DB call commented out
        # data = request.form
        # try:
        #     user = AuthService.register(
        #         username=data.get('username'),
        #         password=data.get('password'),
        #         full_name=data.get('full_name')
        #     )
        #     return redirect(url_for('web.login'))
        # except AppError as e:
        #     return render_template('register.html', error=e.message)
    return render_template('register.html')

# ----------------------------------------
# Login
# ----------------------------------------
@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Temporary: redirect to home
        return redirect(url_for('web.home'))

        # Real DB call commented out
        # data = request.form
        # try:
        #     user = AuthService.authenticate(data.get('username'), data.get('password'))
        #     return redirect(url_for('web.home'))
        # except AppError as e:
        #     return render_template('login.html', error=e.message)
    return render_template('login.html')

# ----------------------------------------
# Organization Details
# ----------------------------------------
@web_bp.route('/org/<int:org_id>')
def org_detail(org_id):
    # Fake org data matching Organization.to_dict()
    org = {
        "id": org_id,
        "name": f"Org {org_id}",
        "description": f"Description for Org {org_id}",
        "officers": ["user1","user2"],
        "contact_email": f"org{org_id}@example.com",
        "created_at": "2025-12-01T00:00:00"
    }

    # Real DB call commented out
    # try:
    #     org = OrgService.get_org(org_id)
    #     org = org.to_dict()
    # except AppError as e:
    #     return redirect(url_for('web.home'))

    return render_template('org_detail.html', org=org)

# ----------------------------------------
# Event Details
# ----------------------------------------
@web_bp.route('/event/<int:event_id>')
def event_detail(event_id):
    # Fake event data matching Event.to_dict()
    event = {
        "id": event_id,
        "org_id": 1,
        "title": f"Event {event_id}",
        "description": f"Details for Event {event_id}",
        "location": "Main Hall",
        "start_time": "2025-12-05T10:00:00",
        "end_time": "2025-12-05T12:00:00",
        "created_at": "2025-12-01T00:00:00"
    }

    # Real DB call commented out
    # try:
    #     events = EventService.upcoming_events()
    #     event = next((e for e in events if e['id'] == event_id), None)
    # except AppError as e:
    #     return redirect(url_for('web.home'))

    return render_template('event_detail.html', event=event)
