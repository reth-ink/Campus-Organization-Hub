import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app

app = create_app({'TESTING': True})
with app.test_client() as c:
    with c.session_transaction() as s:
        s['user_id'] = 51
    r = c.get('/orgs/7')
    print('status', r.status_code)
    print('headers', r.headers)
    print('\nbody:\n')
    print(r.get_data(as_text=True))
