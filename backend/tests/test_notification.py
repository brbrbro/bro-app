def test_list_system_notifications_no_auth(client, app):
    from models import db, Notification
    with app.app_context():
        db.session.add(Notification(user_id=None, type='system', title='Sys', content='ok'))
        db.session.commit()
    resp = client.get('/api/notifications')
    assert resp.status_code == 200
    items = resp.get_json()['notifications']
    assert len(items) == 1


def test_list_includes_user_specific_when_auth(client, app, auth_headers):
    from models import db, Notification, User
    with app.app_context():
        user = User.query.first()
        db.session.add(Notification(user_id=None, type='system', title='Sys', content='global'))
        db.session.add(Notification(user_id=user.id, type='tip', title='Personal', content='hey'))
        db.session.commit()
    resp = client.get('/api/notifications', headers=auth_headers)
    titles = [n['title'] for n in resp.get_json()['notifications']]
    assert 'Sys' in titles
    assert 'Personal' in titles


def test_mark_read(client, app, auth_headers):
    from models import db, Notification
    with app.app_context():
        n = Notification(user_id=None, type='system', title='X', content='y')
        db.session.add(n)
        db.session.commit()
        nid = n.id
    resp = client.post(f'/api/notifications/{nid}/read', headers=auth_headers)
    assert resp.status_code == 200
