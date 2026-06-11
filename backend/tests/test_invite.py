def test_bind_invalid_code(client, auth_headers):
    resp = client.post('/api/invite/bind', json={'invite_code': 'XYZ'}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'invalid_code'


def test_bind_self_rejected(client, auth_headers):
    resp = client.post('/api/invite/bind', json={'invite_code': 'BRO000001'}, headers=auth_headers)
    assert resp.status_code == 400


def test_bind_success(client, app):
    resp1 = client.post('/api/users/wx-login', json={'code': 'inviter_code_unique'})
    inviter_token = resp1.get_json()['token']
    inviter_id = resp1.get_json()['user']['id']

    resp2 = client.post('/api/users/wx-login', json={'code': 'invitee_code_unique'})
    invitee_token = resp2.get_json()['token']

    code = f'BRO{str(inviter_id).zfill(6)}'
    resp = client.post('/api/invite/bind', json={'invite_code': code},
                       headers={'Authorization': f'Bearer {invitee_token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['points_awarded_each'] == 50

    profile = client.get('/api/users/profile', headers={'Authorization': f'Bearer {inviter_token}'})
    assert profile.get_json()['points'] == 50


def test_bind_already_bound(client, app):
    resp1 = client.post('/api/users/wx-login', json={'code': 'i1_unique'})
    inviter_id = resp1.get_json()['user']['id']
    resp2 = client.post('/api/users/wx-login', json={'code': 'i2_unique'})
    invitee_token = resp2.get_json()['token']

    code = f'BRO{str(inviter_id).zfill(6)}'
    headers = {'Authorization': f'Bearer {invitee_token}'}
    client.post('/api/invite/bind', json={'invite_code': code}, headers=headers)
    resp = client.post('/api/invite/bind', json={'invite_code': code}, headers=headers)
    assert resp.status_code == 409
