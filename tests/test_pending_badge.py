import os
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.services.membership_service import MembershipService
from app.services.officer_role_service import OfficerRoleService


@pytest.fixture
def app():
    app = create_app({'TESTING': True})
    return app


def test_pending_badge_shown_on_org_page(app):
    # Use test client and session to act as an admin for org 7 (if admin exists) or use default
    client = app.test_client()

    # Ensure there is at least one pending membership for org 7
    # Create a pending membership for a known user (user 1) if not present
    with app.app_context():
        memberships = MembershipService.get_all_memberships()
        found = False
        for m in memberships:
            try:
                if int(m.get('OrgID') or 0) == 7 and (m.get('Status') or '').lower() == 'pending':
                    found = True
                    break
            except Exception:
                continue
        if not found:
            # create a pending membership (may duplicate in CI but cleanup is not necessary for this smoke test)
            MembershipService.create_membership(1, 7, 'Pending')

        # ensure there is an admin officer for org 7 for this test: pick an approved membership and assign Admin role
        admin_membership = None
        for m in memberships:
            try:
                if int(m.get('OrgID') or 0) == 7 and (m.get('Status') or '').lower() == 'approved':
                    admin_membership = m
                    break
            except Exception:
                continue
        if admin_membership:
            # assign Admin role (this will create/update officer_roles)
            OfficerRoleService.assign_role_to_membership(admin_membership.get('MembershipID'), 'Admin', {
                'can_post_announcements': True,
                'can_create_events': True,
                'can_approve_members': True,
                'can_assign_roles': True,
            })
            admin_user_id = int(admin_membership.get('UserID'))
        else:
            # fallback: use user 51 (may not be admin for org 7)
            admin_user_id = 51

    # set session user to the admin we ensured above
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user_id

    resp = client.get('/orgs/7')
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    # badge should be present when pending_count > 0
    assert 'pending-badge' in html