from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services.organization_service import OrgService
from ..services.event_service import EventService
from ..services.announcement_service import AnnouncementService
from ..services.membership_service import MembershipService
from ..services.user_service import UserService
from ..services.officer_role_service import OfficerRoleService
import functools


def login_required(view_func):
    @functools.wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            # redirect to login, preserve next
            next_url = request.path
            return redirect(url_for('web.login') + f'?next={next_url}')
        return view_func(*args, **kwargs)
    return wrapped

bp = Blueprint('web', __name__)

# Use the raw dicts returned by service.get_all_*() so templates can rely on
# canonical model keys (OrgID, OrgName, OrgDescription, EventName, EventDescription, EventDate, etc.)


@bp.route('/')
def home():
    # Pass raw service outputs (lists of dicts using model.to_dict())
    orgs = OrgService.get_all_organizations()
    events = EventService.get_all_events()
    announcements = AnnouncementService.get_all_announcements()

    # joined_orgs: if user logged in, show organizations they're a member of
    joined = []
    user_id = session.get('user_id')
    if user_id:
        memberships = MembershipService.get_all_memberships()
        org_map = {o['OrgID']: o for o in orgs}
        for m in memberships:
            try:
                if int(m.get('UserID')) == int(user_id):
                    org = org_map.get(int(m.get('OrgID')))
                    if org and org not in joined:
                        joined.append(org)
            except Exception:
                continue

    return render_template('home.html', joined_orgs=joined, announcements=announcements, events=events, orgs=orgs)


@bp.route('/orgs/<int:org_id>')
def org_detail(org_id):
    orgs = OrgService.get_all_organizations()
    org = next((o for o in orgs if int(o.get('OrgID')) == org_id), None)
    if not org:
        return redirect(url_for('web.home'))

    org_t = org

    # member count
    memberships = MembershipService.get_all_memberships()
    member_count = sum(1 for m in memberships if int(m.get('OrgID') or 0) == org_id)

    # officers: join officer roles -> memberships -> users
    officers = []
    roles = OfficerRoleService.get_all_officer_roles()
    users = UserService.get_all_users()
    user_map = { u['UserID']: f"{u['FirstName']} {u['LastName']}" for u in users }
    membership_map = { int(m['MembershipID']): m for m in memberships if m.get('MembershipID') }
    for r in roles:
        try:
            mid = int(r.get('MembershipID') or 0)
        except Exception:
            continue
        mem = membership_map.get(mid)
        if mem and int(mem.get('OrgID') or 0) == org_id:
            officers.append({
                'user_name': user_map.get(mem.get('UserID')) or 'Unknown',
                'role_name': r.get('RoleName') or r.get('role_name')
            })

    # announcements and events filtered by org (keep canonical keys)
    announcements = [a for a in AnnouncementService.get_all_announcements() if int(a.get('OrgID') or 0) == org_id]
    events = [e for e in EventService.get_all_events() if int(e.get('OrgID') or 0) == org_id]

    ann_mapped = announcements
    ev_mapped = events

    is_officer = False
    # very simple check: if any officer entry's user_name corresponds to session user
    if session.get('user_id'):
        uid = session.get('user_id')
        for o in officers:
            # compare by username heuristic
            if str(uid) in str(o.get('user_name')):
                is_officer = True
                break

    return render_template('org_detail.html', org=org_t, member_count=member_count, officers=officers, announcements=ann_mapped, events=ev_mapped, is_officer=is_officer)


@bp.route('/events/<int:event_id>')
def event_detail(event_id):
    events = EventService.get_all_events()
    ev = next((e for e in events if int(e.get('EventID') or 0) == event_id), None)
    if not ev:
        return redirect(url_for('web.home'))
    return render_template('event_detail.html', event=ev)


@bp.route('/create_org', methods=['GET', 'POST'])
@login_required
def create_org():
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('description')
        if not name:
            error = 'Name is required'
        else:
            OrgService.create_organization(name, desc)
            return redirect(url_for('web.home'))
    return render_template('create_org.html', error=error)


@bp.route('/create_event', methods=['GET', 'POST'])
@bp.route('/orgs/<int:org_id>/create_event', methods=['GET', 'POST'])
@login_required
def create_event(org_id=None):
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('description')
        date = request.form.get('event_date')
        location = request.form.get('location')
        if not name or not date:
            error = 'Name and date are required'
        else:
            EventService.create_event(name, desc, date, org_id)
            return redirect(url_for('web.home'))
    return render_template('create_event.html', error=error)


@bp.route('/orgs/<int:org_id>/create_announcement', methods=['GET', 'POST'])
@login_required
def create_announcement(org_id):
    error = None
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            error = 'Title and content required'
        else:
            AnnouncementService.create_announcement(org_id, session.get('user_id'), title, content, None)
            return redirect(url_for('web.org_detail', org_id=org_id))
    return render_template('create_announcement.html', error=error)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # look up raw user row to get PasswordHash and verify
        row = UserService.get_user_row_by_email(email)
        if not row:
            error = 'Invalid credentials'
        else:
            pwd_hash = row.get('PasswordHash')
            if not pwd_hash or not UserService.verify_password(password, pwd_hash):
                error = 'Invalid credentials'
            else:
                session['user_id'] = row.get('UserID')
                # honor next param if present
                next_url = request.args.get('next')
                return redirect(next_url or url_for('web.home'))
    return render_template('login.html', error=error)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        first = request.form.get('first_name')
        last = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not first or not last or not email or not password:
            error = 'All fields are required'
        else:
            UserService.create_user(first, last, email, password)
            # set session to new user
            row = UserService.get_user_row_by_email(email)
            if row:
                session['user_id'] = row.get('UserID')
            return redirect(url_for('web.home'))
    return render_template('register.html', error=error)


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('web.home'))
