def test_leaderboard_empty(client):
    resp = client.get('/api/leaderboard')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ranking'] == []
    assert data['metric'] == 'correct'


def test_leaderboard_metric_total(client):
    resp = client.get('/api/leaderboard?metric=total')
    assert resp.status_code == 200
    assert resp.get_json()['metric'] == 'total'


def test_leaderboard_period_week(client):
    resp = client.get('/api/leaderboard?period=week')
    assert resp.status_code == 200
    assert resp.get_json()['period'] == 'week'


def test_leaderboard_period_month(client):
    resp = client.get('/api/leaderboard?period=month')
    assert resp.status_code == 200
    assert resp.get_json()['period'] == 'month'
