import json


def _create_parsed(app):
    from models import db, ImportBatch, ParsedQuestion
    with app.app_context():
        batch = ImportBatch(source_type='txt', source_file='x.txt', source_url='', status='reviewing')
        db.session.add(batch)
        db.session.commit()
        pq = ParsedQuestion(
            batch_id=batch.id,
            raw_content='{}',
            content='1+1=?',
            options=json.dumps([]),
            answer='2',
            explanation='',
            exam_type='gaokao',
            subject='数学',
            grade='高一',
            knowledge_point='计算',
            type='blank',
            difficulty=1,
            confidence=0.9,
            status='pending'
        )
        db.session.add(pq)
        db.session.commit()
        return batch.id, pq.id


def test_update_parsed_question(client, app):
    _, pid = _create_parsed(app)
    resp = client.put(f'/api/import/parsed/{pid}', json={'content': '2+2=?', 'answer': '4'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['question']['content'] == '2+2=?'
    assert body['question']['answer'] == '4'


def test_manual_approve_completes_batch_when_no_pending_remain(client, app):
    from models import db, ImportBatch, Question
    batch_id, pid = _create_parsed(app)
    resp = client.post(f'/api/import/question/{pid}/approve', json={
        'content': '1+1=?',
        'options': [],
        'answer': '2',
        'explanation': '',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '计算',
        'type': 'blank',
        'difficulty': 1,
        'region': 'mainland'
    })
    assert resp.status_code == 200
    with app.app_context():
        batch = db.session.get(ImportBatch, batch_id)
        assert batch.status == 'completed'
        assert batch.approved_questions == 1
        assert Question.query.count() == 1


def test_split_parsed_question(client, app):
    _, pid = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid}/split', json={
        'first': {'content': '1+1=?', 'answer': '2'},
        'second': {'content': '2+2=?', 'answer': '4'}
    })
    assert resp.status_code == 200
    assert resp.get_json()['created_id']


def test_merge_parsed_questions(client, app):
    batch_id, pid1 = _create_parsed(app)
    from models import db, ParsedQuestion
    with app.app_context():
        pq = ParsedQuestion(
            batch_id=batch_id,
            raw_content='{}',
            content='2+2=?',
            options=json.dumps([]),
            answer='4',
            explanation='',
            exam_type='gaokao',
            subject='数学',
            grade='高一',
            knowledge_point='计算',
            type='blank',
            difficulty=1,
            confidence=0.9,
            status='pending'
        )
        db.session.add(pq)
        db.session.commit()
        pid2 = pq.id
    resp = client.post(f'/api/import/parsed/{pid2}/merge', json={'target_id': pid1})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_split_updates_batch_counts(client, app):
    batch_id, pid = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid}/split', json={
        'first': {'content': '1+1=?', 'answer': '2'},
        'second': {'content': '2+2=?', 'answer': '4'}
    })
    assert resp.status_code == 200
    from models import db, ImportBatch
    with app.app_context():
        batch = db.session.get(ImportBatch, batch_id)
        assert batch.total_questions == 1
        assert batch.parsed_questions == 1


def test_merge_rejects_self(client, app):
    _, pid = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid}/merge', json={'target_id': pid})
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'cannot_merge_self'


def test_merge_rejects_cross_batch(client, app):
    _, pid1 = _create_parsed(app)
    _, pid2 = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid2}/merge', json={'target_id': pid1})
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'different_batch'


def test_approve_safe_keeps_reviewing_when_pending_remain(client, app):
    from models import db, ParsedQuestion, ImportBatch
    batch_id, pid = _create_parsed(app)
    with app.app_context():
        low = ParsedQuestion(
            batch_id=batch_id, raw_content='{}', content='low', options='[]', answer='x',
            explanation='', exam_type='gaokao', subject='数学', grade='高一',
            knowledge_point='计算', type='blank', difficulty=1, confidence=0.2, status='pending'
        )
        db.session.add(low)
        db.session.commit()
    resp = client.post(f'/api/import/batch/{batch_id}/approve-safe', json={'min_confidence': 0.8})
    assert resp.status_code == 200
    with app.app_context():
        batch = db.session.get(ImportBatch, batch_id)
        assert batch.status == 'reviewing'


def test_approve_safe_approves_high_confidence(client, app):
    batch_id, pid = _create_parsed(app)
    resp = client.post(f'/api/import/batch/{batch_id}/approve-safe', json={'min_confidence': 0.8})
    assert resp.status_code == 200
    assert resp.get_json()['approved_count'] == 1


def test_approve_safe_missing_batch_returns_404(client):
    resp = client.post('/api/import/batch/999/approve-safe', json={'min_confidence': 0.8})
    assert resp.status_code == 404
    assert resp.get_json()['error'] == 'not_found'


def test_split_preserves_first_metadata_and_second_metadata(client, app):
    batch_id, pid = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid}/split', json={
        'first': {
            'content': '第一题',
            'answer': 'A',
            'options': [{'key': 'A', 'text': '甲'}],
            'type': 'choice',
            'difficulty': 2,
            'formula_latex': ['x^2=4'],
            'formula_images': ['/static/f1.png'],
            'images': [{'url': '/static/i1.png'}]
        },
        'second': {
            'content': '第二题',
            'answer': 'B',
            'options': [{'key': 'B', 'text': '乙'}],
            'type': 'choice',
            'difficulty': 3,
            'formula_latex': ['y=1'],
            'formula_images': ['/static/f2.png'],
            'images': [{'url': '/static/i2.png'}],
            'raw_ocr_text': '2. 第二题',
            'confidence_detail': {'text': 0.8}
        }
    })
    assert resp.status_code == 200
    created_id = resp.get_json()['created_id']

    from models import db, ParsedQuestion
    with app.app_context():
        first = db.session.get(ParsedQuestion, pid)
        second = db.session.get(ParsedQuestion, created_id)
        assert json.loads(first.options)[0]['key'] == 'A'
        assert json.loads(first.formula_latex) == ['x^2=4']
        assert json.loads(second.options)[0]['key'] == 'B'
        assert json.loads(second.formula_latex) == ['y=1']
        assert second.raw_ocr_text == '2. 第二题'


def test_merge_preserves_source_metadata(client, app):
    batch_id, pid1 = _create_parsed(app)
    from models import db, ParsedQuestion
    with app.app_context():
        source = ParsedQuestion(
            batch_id=batch_id,
            raw_content='{}',
            content='source content',
            options=json.dumps([]),
            answer='B',
            explanation='source explanation',
            exam_type='gaokao',
            subject='数学',
            grade='高一',
            knowledge_point='计算',
            type='blank',
            difficulty=1,
            confidence=0.9,
            status='pending',
            raw_ocr_text='2. source raw',
            images=json.dumps([{'url': '/static/i2.png'}]),
            formula_latex=json.dumps(['z=3']),
            formula_images=json.dumps(['/static/f3.png'])
        )
        db.session.add(source)
        db.session.commit()
        pid2 = source.id

    resp = client.post(f'/api/import/parsed/{pid2}/merge', json={'target_id': pid1})
    assert resp.status_code == 200

    with app.app_context():
        target = db.session.get(ParsedQuestion, pid1)
        merged = db.session.get(ParsedQuestion, pid2)
        assert 'source content' in target.content
        assert 'source raw' in target.raw_ocr_text
        assert json.loads(target.images)[0]['url'] == '/static/i2.png'
        assert json.loads(target.formula_latex) == ['z=3']
        assert merged.status == 'rejected'
