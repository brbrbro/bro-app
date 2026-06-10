def test_today_status_default(client, auth_headers):
    resp = client.get('/api/checkin/today', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['already_checked'] is False
    assert data['points'] == 0


def test_first_checkin_succeeds(client, auth_headers):
    resp = client.post('/api/checkin', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['streak'] == 1
    assert data['points_awarded'] >= 10
    assert data['total_points'] >= 10


def test_double_checkin_returns_409(client, auth_headers):
    client.post('/api/checkin', headers=auth_headers)
    resp = client.post('/api/checkin', headers=auth_headers)
    assert resp.status_code == 409
    assert resp.get_json()['error'] == 'already_checked'


def test_profile_returns_points_after_checkin(client, auth_headers):
    client.post('/api/checkin', headers=auth_headers)
    resp = client.get('/api/users/profile', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['points'] >= 10
    assert 'level' in data
