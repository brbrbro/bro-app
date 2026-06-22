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


def _make_batch(app, status='reviewing'):
    from models import db, ImportBatch, ParsedQuestion
    with app.app_context():
        batch = ImportBatch(
            source_type='txt', source_file='sample.txt', source_url='', status=status,
            exam_type='gaokao', subject='数学', grade='高一', knowledge_point='计算',
            total_questions=2, parsed_questions=2, approved_questions=1
        )
        db.session.add(batch)
        db.session.commit()
        pq = ParsedQuestion(
            batch_id=batch.id, raw_content='{}', content='1+1=?', options='[]',
            answer='2', explanation='', exam_type='gaokao', subject='数学', grade='高一',
            knowledge_point='计算', type='blank', difficulty=1, confidence=0.9, status='pending'
        )
        db.session.add(pq)
        db.session.commit()
        return batch.id


def test_admin_import_batch_detail(client, app):
    batch_id = _make_batch(app)
    resp = client.get(f'/api/admin/import/batches/{batch_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['id'] == batch_id
    assert data['parsed_questions'] == 2


def test_admin_delete_batch_deletes_parsed_only(client, app):
    from models import ParsedQuestion
    batch_id = _make_batch(app)
    resp = client.delete(f'/api/admin/import/batches/{batch_id}')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    with app.app_context():
        assert ParsedQuestion.query.filter_by(batch_id=batch_id).count() == 0


def test_admin_reparse_missing_source_returns_400(client, app):
    batch_id = _make_batch(app)
    resp = client.post(f'/api/admin/import/batches/{batch_id}/reparse')
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'source_file_missing'
