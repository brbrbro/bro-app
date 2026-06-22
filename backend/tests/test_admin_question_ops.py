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


def _make_question(app, content='1+1=?', subject='数学', status='approved'):
    from models import db, Question
    with app.app_context():
        q = Question(
            region='mainland', subject=subject, grade='高一', knowledge_point='计算',
            type='blank', difficulty=1, content=content, answer='2', explanation='基础计算',
            options='[]', source='seed', status=status
        )
        db.session.add(q)
        db.session.commit()
        return q.id


def test_admin_questions_list_filter_keyword(client, app):
    _make_question(app, content='苹果题')
    _make_question(app, content='香蕉题')
    resp = client.get('/api/admin/questions?keyword=苹果')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 1
    assert '苹果' in data['questions'][0]['content']


def test_admin_question_detail_and_update(client, app):
    qid = _make_question(app)
    detail = client.get(f'/api/admin/questions/{qid}')
    assert detail.status_code == 200
    resp = client.put(f'/api/admin/questions/{qid}', json={'answer': '二', 'difficulty': 2})
    assert resp.status_code == 200
    assert resp.get_json()['question']['answer'] == '二'
    assert resp.get_json()['question']['difficulty'] == 2


def test_admin_question_archive_and_delete(client, app):
    qid = _make_question(app)
    archive = client.post(f'/api/admin/questions/{qid}/archive')
    assert archive.status_code == 200
    assert archive.get_json()['question']['status'] == 'archived'
    delete = client.delete(f'/api/admin/questions/{qid}')
    assert delete.status_code == 200


def test_admin_quality_detects_missing_answer_and_explanation(client, app):
    _make_question(app, content='缺答案题')
    from models import db, Question
    with app.app_context():
        q = Question.query.filter_by(content='缺答案题').first()
        q.answer = ''
        q.explanation = ''
        db.session.commit()
    resp = client.get('/api/admin/quality/issues')
    assert resp.status_code == 200
    issue_types = [i['issue_type'] for i in resp.get_json()['issues']]
    assert 'missing_answer' in issue_types
    assert 'missing_explanation' in issue_types


def test_admin_quality_detects_duplicate_content(client, app):
    _make_question(app, content='重复题')
    _make_question(app, content='重复题')
    resp = client.get('/api/admin/quality/issues?issue_type=duplicate_content')
    assert resp.status_code == 200
    assert resp.get_json()['issues'][0]['issue_type'] == 'duplicate_content'
