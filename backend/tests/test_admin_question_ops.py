import json
from datetime import datetime, timezone, timedelta


def test_admin_import_batches_empty(client):
    resp = client.get('/api/admin/import/batches')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['batches'] == []
    assert data['total'] == 0


def test_admin_import_stats_empty(client):
    resp = client.get('/api/admin/import/stats')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['totals']['batches'] == 0
    assert data['totals']['parsed_questions'] == 0
