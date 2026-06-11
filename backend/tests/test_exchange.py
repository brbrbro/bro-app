def test_list_items_public(client):
    resp = client.get('/api/exchange/items')
    assert resp.status_code == 200
    items = resp.get_json()['items']
    assert any(i['id'] == 1 for i in items)


def test_redeem_insufficient_points(client, auth_headers):
    resp = client.post('/api/exchange', json={'item_id': 1}, headers=auth_headers)
    assert resp.status_code == 409
    assert resp.get_json()['error'] == 'insufficient_points'


def test_redeem_success(client, auth_headers, app):
    from models import db, User
    with app.app_context():
        user = User.query.first()
        user.points = 100
        db.session.commit()
    resp = client.post('/api/exchange', json={'item_id': 1}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['cost_paid'] == 50
    assert data['remaining_points'] == 50


def test_redeem_invalid_item(client, auth_headers):
    resp = client.post('/api/exchange', json={'item_id': 999}, headers=auth_headers)
    assert resp.status_code == 400
