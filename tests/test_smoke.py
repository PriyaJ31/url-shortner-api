import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

def test_home_route():
    app = create_app()
    client = app.test_client()
    res = client.get('/')
    assert res.status_code == 200

def test_shorten_missing_url():
    app = create_app()
    client = app.test_client()
    res = client.post('/shorten', json={})
    assert res.status_code == 400
    assert "error" in res.get_json()
