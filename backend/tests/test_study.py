def test_submit_session_requires_positive(client, auth_headers):
    resp = client.post('/api/study/session', json={'seconds': 0}, headers=auth_headers)
    assert resp.status_code == 400


def test_submit_and_today(client, auth_headers):
    client.post('/api/study/session', json={'seconds': 60}, headers=auth_headers)
    client.post('/api/study/session', json={'seconds': 90}, headers=auth_headers)
    resp = client.get('/api/study/today', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['today_seconds'] == 150
    assert data['today_minutes'] == 2


def test_today_empty(client, auth_headers):
    resp = client.get('/api/study/today', headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()['today_seconds'] == 0
