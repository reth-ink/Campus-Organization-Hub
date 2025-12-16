import os
import tempfile
import sqlite3
import pytest
from app import create_app


@pytest.fixture
def client():
    # create a temp copy of the DB so tests don't modify real data
    src = os.path.join(os.getcwd(), 'campus_hub.db')
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn_src = sqlite3.connect(src)
    conn_dst = sqlite3.connect(path)
    with conn_dst:
        conn_src.backup(conn_dst)
    conn_src.close()
    conn_dst.close()

    # set environment to use the temp DB via app config
    app = create_app({'TESTING': True, 'DATABASE': path})
    with app.test_client() as client:
        yield client


def test_admin_page_requires_login(client):
    # Try to GET admin page without login
    rv = client.get('/orgs/1/admin', follow_redirects=False)
    assert rv.status_code in (302, 301)

# Additional tests (approve membership / assign role) would require creating a session user and
# setting up a membership; those are left as next steps for deeper integration tests.
