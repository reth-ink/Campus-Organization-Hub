import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app

app = create_app()
app.testing = True

with app.test_client() as c:
    # set session user_id to admin (51)
    with c.session_transaction() as sess:
        sess['user_id'] = 51
    resp = c.get('/orgs/21')
    html = resp.get_data(as_text=True)
    has_toggle = 'id="org-settings-toggle"' in html
    has_cancel_disabled = 'id="org-settings-cancel" class="post-button btn-disabled"' in html
    has_cancel_enabled = 'id="org-settings-cancel" class="post-button"' in html
    print('status_code:', resp.status_code)
    print('has_toggle:', has_toggle)
    print('cancel_disabled_class_present:', has_cancel_disabled)
    print('cancel_enabled_class_present:', has_cancel_enabled)
    # show small snippet
    start = html.find('id="org-settings-toggle"')
    if start!=-1:
        print('\nSnippet around toggle:')
        print(html[start-80:start+120])
