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
    _, pid2 = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid2}/merge', json={'target_id': pid1})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_approve_safe_approves_high_confidence(client, app):
    batch_id, pid = _create_parsed(app)
    resp = client.post(f'/api/import/batch/{batch_id}/approve-safe', json={'min_confidence': 0.8})
    assert resp.status_code == 200
    assert resp.get_json()['approved_count'] == 1
