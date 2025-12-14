from flask import Blueprint, render_template, request, redirect, url_for, session
from ..services.org_service import OrgService
from ..services.event_service import EventService
from ..services.announcement_service import AnnouncementService
from ..services.auth_service import AuthService
from ..services.errors import AppError

web_bp = Blueprint('web', __name__)

# -------------------- HOME --------------------
@web_bp.route('/')
def home():
    try:
        orgs = OrgService.search_orgs()
        return render_template('home.html', orgs=orgs)
    except AppError as e:
        return render_template('home.html', error=e.message)

# -------------------- REGISTER --------------------
@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        try:
            user = AuthService.register(
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                email=data.get('email'),
                password=data.get('password')
            )
            session['user_id'] = user.UserID
            return redirect(url_for('web.home'))
        except AppError as e:
            return render_template('register.html', error=e.message)
    return render_template('register.html')

# -------------------- LOGIN --------------------
@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        try:
            user = AuthService.login(email=data.get('email'), password=data.get('password'))
            session['user_id'] = user.UserID
            return redirect(url_for('web.home'))
        except AppError as e:
            return render_template('login.html', error=e.message)
    return render_template('login.html')

# -------------------- LOGOUT --------------------
@web_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('web.home'))

# -------------------- CREATE ORGANIZATION --------------------
@web_bp.route('/org/create', methods=['GET', 'POST'])
def create_org():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))

    if request.method == 'POST':
        data = request.form
        try:
            org = OrgService.create_org(
                name=data.get('name'),
                description=data.get('description'),
                creator_id=session['user_id']
            )
            return redirect(url_for('web.org_detail', org_id=org.OrgID))
        except AppError as e:
            return render_template('create_org.html', error=e.message)
    return render_template('create_org.html')

# -------------------- ORG DETAIL --------------------
@web_bp.route('/org/<int:org_id>')
def org_detail(org_id):
    org = OrgService.get_org(org_id)

    # Member count
    org.member_count = len(org.memberships) if hasattr(org, 'memberships') else 0

    # Officers
    org.officers = []
    for m in org.memberships:
        for o in m.officer_roles:
            org.officers.append({"name": m.user.FirstName + " " + m.user.LastName, "role": o.RoleName})

    # Announcements
    announcements = AnnouncementService.get_org_announcements(org_id)
    for ann in announcements:
        ann.creator_name = ann.creator.membership.user.FirstName + " " + ann.creator.membership.user.LastName
    org.announcements = announcements

    # Check if current user is officer
    user_id = session.get('user_id')
    is_officer = False
    if user_id:
        for m in org.memberships:
            if m.UserID == user_id and m.officer_roles:
                is_officer = True
                break

    return render_template('org_detail.html', org=org, is_officer=is_officer)

# -------------------- CREATE ANNOUNCEMENT --------------------
@web_bp.route('/org/<int:org_id>/announcement/create', methods=['GET', 'POST'])
def create_announcement(org_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))

    if request.method == 'POST':
        data = request.form
        try:
            AnnouncementService.create_announcement(
                org_id=org_id,
                user_id=session['user_id'],
                title=data.get('title'),
                content=data.get('content')
            )
            return redirect(url_for('web.org_detail', org_id=org_id))
        except AppError as e:
            return render_template('create_announcement.html', org_id=org_id, error=e.message)
    return render_template('create_announcement.html', org_id=org_id)

# -------------------- CREATE EVENT --------------------
@web_bp.route('/org/<int:org_id>/event/create', methods=['GET', 'POST'])
def create_event(org_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))

    if request.method == 'POST':
        data = request.form
        try:
            EventService.create_event(
                org_id=org_id,
                user_id=session['user_id'],
                name=data.get('name'),
                description=data.get('description'),
                event_date=data.get('event_date'),
                location=data.get('location')
            )
            return redirect(url_for('web.org_detail', org_id=org_id))
        except AppError as e:
            return render_template('create_event.html', org_id=org_id, error=e.message)
    return render_template('create_event.html', org_id=org_id)
