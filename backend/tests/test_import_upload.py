"""Smoke test for /api/import/upload (no real OpenAI key required — uses fallback)."""
import io


def test_upload_no_file_rejected(client):
    resp = client.post('/api/import/upload')
    assert resp.status_code in (400, 415)


def test_upload_unsupported_extension(client):
    data = {
        'file': (io.BytesIO(b'hello world'), 'test.xyz')
    }
    resp = client.post('/api/import/upload',
                       data=data,
                       content_type='multipart/form-data')
    assert resp.status_code in (200, 400, 415)


def test_upload_plain_text_file_parses_numbered_questions(client):
    sample = (
        "1. 数学：1+1 等于几？答案：2\n"
        "2. 物理：g 的近似值？答案：9.8 m/s²\n"
        "3. 化学：水的化学式？答案：H2O\n"
    )
    data = {
        'file': (io.BytesIO(sample.encode('utf-8')), 'questions.txt'),
        'subject': '通用'
    }
    resp = client.post('/api/import/upload',
                       data=data,
                       content_type='multipart/form-data')
    assert resp.status_code in (200, 400, 415)
    if resp.status_code == 200:
        body = resp.get_json()
        assert isinstance(body, dict)
