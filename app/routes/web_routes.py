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


def _resolve_creator_name(created_by, user_map):
    """Resolve a CreatedBy value to a human-friendly name.
    CreatedBy may be a UserID or an OfficerRoleID. Try user_map first, then
    fall back to resolving officer_role -> membership -> user.
    """
    if created_by is None:
        return None
    try:
        cid = int(created_by)
    except Exception:
        return None

    # direct user id mapping
    if cid in user_map:
        return user_map[cid]

    # fall back: CreatedBy may be an OfficerRoleID
    orow = OfficerRoleService.get_user_by_officer_role(cid)
    if orow:
        return f"{orow.get('FirstName')} {orow.get('LastName')}"

    return None

# Use the raw dicts returned by service.get_all_*() so templates can rely on
# canonical model keys (OrgID, OrgName, OrgDescription, EventName, EventDescription, EventDate, etc.)


@bp.route('/')
def home():
    # Pass raw service outputs (lists of dicts using model.to_dict())
    orgs = OrgService.get_all_organizations()
    events = EventService.get_all_events()
    announcements = AnnouncementService.get_all_announcements()
    # show newest announcements first (DatePosted or created_at)
    try:
        announcements = sorted(announcements, key=lambda a: a.get('DatePosted') or a.get('created_at') or '', reverse=True)
    except Exception:
        # fallback: leave order unchanged
        pass

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

    # member count (only count approved memberships, exclude pending/rejected)
    memberships = MembershipService.get_all_memberships()
    def _get_status(m):
        try:
            return (m.get('Status') or m.get('status') or '').lower()
        except Exception:
            return ''
    def _is_approved(m):
        return _get_status(m) == 'approved'
    def _is_pending(m):
        return _get_status(m) == 'pending'

    member_count = sum(1 for m in memberships if int(m.get('OrgID') or 0) == org_id and _is_approved(m))
    pending_count = sum(1 for m in memberships if int(m.get('OrgID') or 0) == org_id and _is_pending(m))

    # officers: fetch via service helper which joins officer_roles -> memberships -> users
    officers = OfficerRoleService.get_officers_by_org(org_id)

    # announcements and events filtered by org (keep canonical keys)
    announcements = [a for a in AnnouncementService.get_all_announcements() if int(a.get('OrgID') or 0) == org_id]
    try:
        announcements = sorted(announcements, key=lambda a: a.get('DatePosted') or a.get('created_at') or '', reverse=True)
    except Exception:
        pass
    events = [e for e in EventService.get_all_events() if int(e.get('OrgID') or 0) == org_id]

    # map announcement creators as well (they may be officer role ids)
    ann_mapped = []
    for a in announcements:
        ad = dict(a)
        # try to resolve CreatedBy to a human-friendly name
        users = UserService.get_all_users()
        user_map_local = { u['UserID']: f"{u['FirstName']} {u['LastName']}" for u in users }
        ad['CreatorName'] = _resolve_creator_name(a.get('CreatedBy'), user_map_local)
        ann_mapped.append(ad)
    # Map events into the shape the template expects (Description key and CreatorName)
    users = UserService.get_all_users()
    user_map = { u['UserID']: f"{u['FirstName']} {u['LastName']}" for u in users }
    ev_mapped = [
        {
            'EventID': e.get('EventID'),
            'EventName': e.get('EventName'),
            'Description': e.get('EventDescription') or e.get('Description'),
            'EventDate': e.get('EventDate'),
            'Location': e.get('Location'),
            'CreatedBy': e.get('CreatedBy'),
            'CreatorName': _resolve_creator_name(e.get('CreatedBy'), user_map)
        }
        for e in events
    ]

    is_officer = False
    # check if the current session user has admin/officer permissions for this org
    if session.get('user_id'):
        uid = session.get('user_id')
        # mark is_officer true if any officer entry's UserID equals uid and role grants admin-ish permissions
        for o in officers:
            try:
                if int(o.get('UserID') or 0) == int(uid):
                    # if they have any of the admin permissions, treat as officer
                    if o.get('can_approve_members') or o.get('can_assign_roles') or o.get('can_post_announcements') or o.get('can_create_events'):
                        is_officer = True
                        break
            except Exception:
                continue

    # Determine current user's membership for this org (if any)
    user_membership = None
    if session.get('user_id'):
        try:
            uid = int(session.get('user_id'))
            memberships = MembershipService.get_all_memberships()
            for m in memberships:
                try:
                    if int(m.get('UserID') or 0) == uid and int(m.get('OrgID') or 0) == org_id:
                        user_membership = m
                        break
                except Exception:
                    continue
        except Exception:
            user_membership = None

    # Determine whether current user is an admin (has assign/approve permissions)
    is_admin = False
    if session.get('user_id'):
        try:
            uid = session.get('user_id')
            perms = OfficerRoleService.user_permissions_for_org(org_id, uid)
            is_admin = bool(perms.get('can_assign_roles') or perms.get('can_approve_members'))
        except Exception:
            is_admin = False

    return render_template('org_detail.html', org=org_t, member_count=member_count, pending_count=pending_count, officers=officers, announcements=ann_mapped, events=ev_mapped, is_officer=is_officer, is_admin=is_admin, user_membership=user_membership)


@bp.route('/orgs/<int:org_id>/admin')
@login_required
def org_admin(org_id):
    # Verify org exists
    orgs = OrgService.get_all_organizations()
    org = next((o for o in orgs if int(o.get('OrgID')) == org_id), None)
    if not org:
        return redirect(url_for('web.home'))

    # Check current user's permissions
    user_id = session.get('user_id')
    perms = OfficerRoleService.user_permissions_for_org(org_id, user_id) if user_id else {'can_approve_members': 0, 'can_assign_roles': 0}
    if not (perms.get('can_approve_members') or perms.get('can_assign_roles')):
        # not authorized
        return redirect(url_for('web.org_detail', org_id=org_id))

    # memberships for this org
    memberships = MembershipService.get_memberships_by_org(org_id)
    users = UserService.get_all_users()
    user_map = { u['UserID']: f"{u['FirstName']} {u['LastName']}" for u in users }

    # annotate memberships with user names
    for m in memberships:
        try:
            m['user_name'] = user_map.get(int(m.get('UserID'))) or 'Unknown'
        except Exception:
            m['user_name'] = 'Unknown'

    pending = [m for m in memberships if (m.get('Status') or '').lower() == 'pending']

    # fetch current officers for sidebar using join helper
    officers = OfficerRoleService.get_officers_by_org(org_id)

    member_count = sum(1 for m in memberships if (m.get('Status') or '').lower() == 'approved')

    return render_template('org_admin.html', org=org, memberships=memberships, pending_memberships=pending, officers=officers, member_count=member_count)


@bp.route('/orgs/<int:org_id>/admin/approve', methods=['POST'])
@login_required
def approve_membership(org_id):
    user_id = session.get('user_id')
    perms = OfficerRoleService.user_permissions_for_org(org_id, user_id) if user_id else {}
    if not perms.get('can_approve_members'):
        return redirect(url_for('web.org_detail', org_id=org_id))

    membership_id = request.form.get('membership_id')
    action = request.form.get('action')
    if membership_id and action:
        if action == 'approve':
            MembershipService.update_membership_status(membership_id, 'Approved')
            flash('Membership approved')
        else:
            MembershipService.update_membership_status(membership_id, 'Rejected')
            flash('Membership rejected')

    return redirect(url_for('web.org_admin', org_id=org_id))


@bp.route('/orgs/<int:org_id>/admin/assign_role', methods=['POST'])
@login_required
def assign_role(org_id):
    user_id = session.get('user_id')
    perms = OfficerRoleService.user_permissions_for_org(org_id, user_id) if user_id else {}
    if not perms.get('can_assign_roles'):
        return redirect(url_for('web.org_detail', org_id=org_id))

    membership_id = request.form.get('membership_id')
    role_name = request.form.get('role_name')
    permissions = {
        'can_post_announcements': bool(request.form.get('can_post_announcements')),
        'can_create_events': bool(request.form.get('can_create_events')),
        'can_approve_members': bool(request.form.get('can_approve_members')),
        'can_assign_roles': bool(request.form.get('can_assign_roles')),
    }
    if membership_id and role_name:
        OfficerRoleService.assign_role_to_membership(membership_id, role_name, permissions)
        flash('Role assigned')

    return redirect(url_for('web.org_admin', org_id=org_id))


@bp.route('/orgs/<int:org_id>/settings/update', methods=['POST'])
@login_required
def org_update_settings(org_id):
    # Only allow users with role assignment permission to rename/change description
    user_id = session.get('user_id')
    perms = OfficerRoleService.user_permissions_for_org(org_id, user_id) if user_id else {}
    if not perms.get('can_assign_roles'):
        flash('You do not have permission to change organization settings')
        return redirect(url_for('web.org_detail', org_id=org_id))

    name = request.form.get('org_name')
    desc = request.form.get('org_description')
    try:
        OrgService.update_organization(org_id, name=name, description=desc)
        flash('Organization settings updated')
    except Exception as e:
        flash(str(e))
    return redirect(url_for('web.org_detail', org_id=org_id))


@bp.route('/orgs/<int:org_id>/settings/delete', methods=['POST'])
@login_required
def org_delete(org_id):
    # Only allow users with role assignment permission to delete org
    user_id = session.get('user_id')
    perms = OfficerRoleService.user_permissions_for_org(org_id, user_id) if user_id else {}
    if not perms.get('can_assign_roles'):
        flash('You do not have permission to delete this organization')
        return redirect(url_for('web.org_detail', org_id=org_id))

    try:
        OrgService.delete_organization(org_id)
        flash('Organization deleted')
    except Exception as e:
        flash(str(e))
        return redirect(url_for('web.org_detail', org_id=org_id))

    return redirect(url_for('web.home'))


@bp.route('/orgs/<int:org_id>/join', methods=['POST'])
@login_required
def request_join(org_id):
    """Handle a user's request to join an organization. Creates a membership with status 'Pending' if none exists."""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('web.login') + f'?next={request.path}')

    # check existing membership
    existing = None
    memberships = MembershipService.get_all_memberships()
    for m in memberships:
        try:
            if int(m.get('UserID') or 0) == int(user_id) and int(m.get('OrgID') or 0) == org_id:
                existing = m
                break
        except Exception:
            continue

    if existing:
        status = (existing.get('Status') or '').lower()
        if status == 'approved':
            # already a member
            flash('You are already a member of this organization')
        elif status == 'pending':
            flash('Your membership request is already pending')
        else:
            # create another pending request
            MembershipService.create_membership(user_id, org_id, 'Pending')
            flash('Membership request submitted')
    else:
        MembershipService.create_membership(user_id, org_id, 'Pending')
        flash('Membership request submitted')

    return redirect(url_for('web.org_detail', org_id=org_id))


@bp.route('/events/<int:event_id>')
def event_detail(event_id):
    events = EventService.get_all_events()
    ev = next((e for e in events if int(e.get('EventID') or 0) == event_id), None)
    if not ev:
        return redirect(url_for('web.home'))
    # try to map CreatedBy to a human-friendly name when possible
    users = UserService.get_all_users()
    user_map = { u['UserID']: f"{u['FirstName']} {u['LastName']}" for u in users }
    creator_name = _resolve_creator_name(ev.get('CreatedBy'), user_map)
    # attach CreatorName and ensure a 'Description' key for templates
    ev_display = dict(ev)
    ev_display['CreatorName'] = creator_name
    ev_display['Description'] = ev.get('EventDescription') or ev.get('Description') or ''
    return render_template('event_detail.html', event=ev_display)


@bp.route('/events')
def events():
    # list all events (sorted ascending by EventDate when available)
    events = EventService.get_all_events()
    try:
        events = sorted(events, key=lambda e: e.get('EventDate') or '')
    except Exception:
        pass
    # map creator names where possible
    users = UserService.get_all_users()
    user_map = { u['UserID']: f"{u['FirstName']} {u['LastName']}" for u in users }
    ev_mapped = []
    for e in events:
        ed = dict(e)
        ed['CreatorName'] = _resolve_creator_name(e.get('CreatedBy'), user_map)
        ed['Description'] = e.get('EventDescription') or e.get('Description') or ''
        ev_mapped.append(ed)
    return render_template('events.html', events=ev_mapped)


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
            # create the organization and ensure the creating user is a member
            org_id = OrgService.create_organization(name, desc)

            # If a user is logged in, make them a member and create an officer role
            user_id = session.get('user_id')
            if user_id and org_id:
                try:
                    # This helper will ensure a membership exists and create an officer role (Admin)
                    OfficerRoleService.get_or_create_officer_role_for_user(org_id, user_id, role_name='Admin')
                except Exception:
                    # membership/officer creation is best-effort — continue to redirect even on failure
                    pass
            flash(f'Organization "{name}" created')
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
            # check permission: user must have can_create_events
            user_id = session.get('user_id')
            created_by = None
            if user_id:
                perms = OfficerRoleService.user_permissions_for_org(org_id, user_id)
                if perms.get('can_create_events'):
                    # ensure an officer role exists (may grant appropriate permissions elsewhere)
                    created_by = OfficerRoleService.get_or_create_officer_role_for_user(org_id, user_id, role_name='Admin')
                else:
                    error = 'You do not have permission to create events for this organization.'

            EventService.create_event(name, desc, date, org_id, created_by, location)
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
            # check permission to post announcement
            user_id = session.get('user_id')
            created_by = None
            if user_id:
                perms = OfficerRoleService.user_permissions_for_org(org_id, user_id)
                if perms.get('can_post_announcements'):
                    created_by = OfficerRoleService.get_or_create_officer_role_for_user(org_id, user_id, role_name='Admin')
                else:
                    error = 'You do not have permission to post announcements for this organization.'

            if not error:
                AnnouncementService.create_announcement(org_id, created_by, title, content, None)
                flash('Announcement posted')
            else:
                flash(error)
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


@bp.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    user = UserService.get_user_row_by_email(user_id) if False else None
    # prefer the UserService helper
    user = UserService.get_user_row_by_id(user_id)
    return render_template('profile.html', user=user)
