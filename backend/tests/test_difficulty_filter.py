def _seed_one(difficulty=3):
    from models import db, Question
    q = Question(
        region='mainland', subject='测试', grade='高一',
        type='choice', difficulty=difficulty,
        content=f'测试题难度{difficulty}', answer='A',
        options='[]', status='approved', source='seed'
    )
    db.session.add(q)
    db.session.commit()
    return q.id


def test_random_filters_by_difficulty(client, app):
    with app.app_context():
        _seed_one(difficulty=1)
        qid3 = _seed_one(difficulty=3)

    resp = client.get('/api/questions/random?difficulty=3')
    assert resp.status_code == 200
    assert resp.get_json()['id'] == qid3


def test_random_no_match_returns_404(client, app):
    resp = client.get('/api/questions/random?difficulty=5')
    assert resp.status_code == 404


def test_submit_with_challenge_doubles_points(client, app, auth_headers):
    with app.app_context():
        qid = _seed_one(difficulty=2)

    resp = client.post('/api/progress', json={
        'question_id': qid, 'user_answer': 'A',
        'is_correct': True, 'is_challenge': True
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['points_awarded'] == 4


def test_submit_normal_correct_awards_base(client, app, auth_headers):
    with app.app_context():
        qid = _seed_one(difficulty=3)

    resp = client.post('/api/progress', json={
        'question_id': qid, 'user_answer': 'A',
        'is_correct': True, 'is_challenge': False
    }, headers=auth_headers)
    assert resp.get_json()['points_awarded'] == 3
