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


def test_admin_reparse_existing_source_creates_parsed_questions(client, app, tmp_path):
    from models import db, ImportBatch, ParsedQuestion
    source = tmp_path / 'questions.txt'
    source.write_text('1. 1+1=?\n答案：2', encoding='utf-8')
    with app.app_context():
        batch = ImportBatch(
            source_type='txt', source_file='questions.txt', source_url=str(source), status='completed',
            exam_type='gaokao', subject='数学', grade='高一', knowledge_point='计算',
            total_questions=0, parsed_questions=0, approved_questions=3
        )
        db.session.add(batch)
        db.session.commit()
        batch_id = batch.id
    resp = client.post(f'/api/admin/import/batches/{batch_id}/reparse')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['batch_id'] == batch_id
    assert data['total_questions'] > 0
    with app.app_context():
        batch = db.session.get(ImportBatch, batch_id)
        assert batch.status == 'reviewing'
        assert batch.approved_questions == 0
        assert ParsedQuestion.query.filter_by(batch_id=batch_id).count() > 0


def _make_question(app, content='1+1=?', subject='数学', status='approved', grade='高一', knowledge_point='计算', type='blank', difficulty=1, source='seed', options='[]'):
    from models import db, Question
    with app.app_context():
        q = Question(
            region='mainland', subject=subject, grade=grade, knowledge_point=knowledge_point,
            type=type, difficulty=difficulty, content=content, answer='2', explanation='基础计算',
            options=options, source=source, status=status
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


def test_admin_questions_filters_grade_type_source(client, app):
    _make_question(app, content='目标题', grade='高二', type='choice', source='import', options='["A", "B"]')
    _make_question(app, content='其他题', grade='高一', type='blank', source='seed')
    resp = client.get('/api/admin/questions?grade=高二&type=choice&source=import')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 1
    assert data['questions'][0]['content'] == '目标题'


def test_admin_questions_filters_knowledge_point_and_difficulty(client, app):
    _make_question(app, content='函数题', knowledge_point='函数', difficulty=3)
    _make_question(app, content='几何题', knowledge_point='几何', difficulty=1)
    resp = client.get('/api/admin/questions?knowledge_point=函数&difficulty=3')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 1
    assert data['questions'][0]['content'] == '函数题'


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


def test_admin_quality_filters_subject_and_paginates(client, app):
    _make_question(app, content='数学缺答案', subject='数学')
    _make_question(app, content='语文缺答案', subject='语文')
    from models import db, Question
    with app.app_context():
        for q in Question.query.all():
            q.answer = ''
        db.session.commit()
    resp = client.get('/api/admin/quality/issues?issue_type=missing_answer&subject=数学&page=1&per_page=1')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 1
    assert data['page'] == 1
    assert data['pages'] == 1
    assert data['issues'][0]['subject'] == '数学'
    assert data['issues'][0]['severity']
    assert data['issues'][0]['suggestion']


def test_admin_quality_invalid_options_only_for_choice_with_too_few_options(client, app):
    _make_question(app, content='选择题', type='choice', options='["A"]')
    _make_question(app, content='填空题', type='blank', options='[]')
    resp = client.get('/api/admin/quality/issues?issue_type=invalid_options')
    assert resp.status_code == 200
    issues = resp.get_json()['issues']
    assert len(issues) == 1
    assert issues[0]['content'] == '选择题'


def test_admin_quality_unknown_type_allows_valid_contract_types(client, app):
    _make_question(app, content='有效选择', type='choice', options='["A", "B"]')
    _make_question(app, content='未知类型', type='unknown')
    _make_question(app, content='非合同类型', type='single')
    resp = client.get('/api/admin/quality/issues?issue_type=unknown_type')
    assert resp.status_code == 200
    issues = resp.get_json()['issues']
    assert len(issues) == 2
    assert {item['content'] for item in issues} == {'未知类型', '非合同类型'}


def test_admin_import_stats_counts_batches(client, app):
    _make_batch(app, status='reviewing')
    _make_batch(app, status='completed')
    resp = client.get('/api/admin/import/stats')
    assert resp.status_code == 200
    totals = resp.get_json()['totals']
    assert totals['batches'] == 2
    assert totals['parsed_questions'] == 4
    assert totals['approved_questions'] == 2
    assert 'by_status' in resp.get_json()


def test_admin_import_stats_group_by_status(client, app):
    _make_batch(app, status='reviewing')
    _make_batch(app, status='completed')
    resp = client.get('/api/admin/import/stats?group_by=status')
    assert resp.status_code == 200
    grouped = {row['key']: row['count'] for row in resp.get_json()['grouped']}
    assert grouped['reviewing'] == 1
    assert grouped['completed'] == 1


def test_admin_import_stats_filters_by_created_at_date(client, app):
    from models import db, ImportBatch
    old_id = _make_batch(app, status='reviewing')
    new_id = _make_batch(app, status='completed')
    with app.app_context():
        db.session.get(ImportBatch, old_id).created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
        db.session.get(ImportBatch, new_id).created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        db.session.commit()
    resp = client.get('/api/admin/import/stats?start=2024-01-01&end=2024-01-02&group_by=day')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['totals']['batches'] == 1
    assert data['grouped'] == [{'key': '2024-01-01', 'count': 1}]
