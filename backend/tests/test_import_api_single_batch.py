import io


def test_single_text_import_creates_one_parsed_question(client):
    resp = client.post('/api/import/single', json={
        'text': '1. 1+1=?\n答案：2',
        'exam_type': 'gaokao',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '计算'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['total_questions'] == 1
    assert data['questions'][0]['answer'] == '2'


def test_single_import_requires_subject(client):
    resp = client.post('/api/import/single', json={'text': '1. hi'})
    assert resp.status_code == 400


def test_batch_txt_import_creates_batch_and_questions(client):
    sample = '1. 1+1=?\n答案：2\n\n2. 2+2=?\n答案：4'
    data = {
        'file': (io.BytesIO(sample.encode('utf-8')), 'questions.txt'),
        'exam_type': 'gaokao',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '计算'
    }
    resp = client.post('/api/import/batch', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['total_questions'] == 2
    assert body['batch_id']
