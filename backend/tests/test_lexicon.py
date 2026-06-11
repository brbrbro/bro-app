def _seed_word(subject='数学'):
    from models import db, LexiconWord
    w = LexiconWord(word='测试词', definition='测试定义', example='测试例句', subject=subject)
    db.session.add(w)
    db.session.commit()
    return w.id


def test_lexicon_empty(client):
    resp = client.get('/api/lexicon')
    assert resp.status_code == 200
    assert resp.get_json()['words'] == []


def test_lexicon_subject_filter(client, app):
    with app.app_context():
        _seed_word(subject='数学')
        _seed_word(subject='物理')

    resp = client.get('/api/lexicon?subject=数学')
    assert resp.status_code == 200
    words = resp.get_json()['words']
    assert len(words) == 1
    assert words[0]['subject'] == '数学'
