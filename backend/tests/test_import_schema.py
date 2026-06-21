import json


def test_parsed_question_supports_recognition_metadata(client, app):
    from models import db, ParsedQuestion

    with app.app_context():
        pq = ParsedQuestion(
            batch_id=1,
            raw_content='{}',
            content='已知 $x^2=4$，求 x。',
            options='[]',
            answer='±2',
            explanation='平方根定义',
            exam_type='gaokao',
            subject='数学',
            grade='高一',
            knowledge_point='方程',
            type='blank',
            difficulty=2,
            status='pending',
            source_page=1,
            bbox=json.dumps({'x': 10, 'y': 20, 'w': 300, 'h': 160}),
            raw_ocr_text='1. 已知 x^2=4，求 x。',
            formula_latex=json.dumps(['x^2=4']),
            formula_images=json.dumps(['/static/images/formula-1.png']),
            confidence_detail=json.dumps({'text': 0.96, 'formula': 0.82, 'layout': 0.9})
        )
        db.session.add(pq)
        db.session.commit()

        saved = ParsedQuestion.query.first()
        assert saved.source_page == 1
        assert json.loads(saved.bbox)['w'] == 300
        assert json.loads(saved.formula_latex) == ['x^2=4']
        assert saved.raw_ocr_text == '1. 已知 x^2=4，求 x。'
        assert json.loads(saved.formula_images) == ['/static/images/formula-1.png']
        assert json.loads(saved.confidence_detail)['formula'] == 0.82


def test_import_recognition_migration_adds_missing_columns(tmp_path, monkeypatch):
    import sqlite3
    import migrate_import_recognition as mig

    db_path = tmp_path / 'bro.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('CREATE TABLE parsed_questions (id INTEGER PRIMARY KEY, images TEXT)')
    conn.commit()
    conn.close()

    monkeypatch.setattr(mig, 'DB_PATH', str(db_path))
    mig.main()

    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute('PRAGMA table_info(parsed_questions)').fetchall()]
    conn.close()

    for name, _ in mig.COLUMNS:
        assert name in cols


def test_question_candidate_to_dict_is_stable():
    from services.import_schema import QuestionCandidate, ImageAsset, FormulaAsset

    candidate = QuestionCandidate(
        index=1,
        content='求 x^2=4 的解。',
        options=[],
        answer='±2',
        explanation='平方根定义',
        question_type='blank',
        difficulty=2,
        source_page=1,
        bbox={'x': 0, 'y': 0, 'w': 100, 'h': 80},
        raw_ocr_text='1. 求 x^2=4 的解。',
        images=[ImageAsset(path='/tmp/q1.png', url='/static/images/q1.png', image_type='diagram')],
        formulas=[FormulaAsset(latex='x^2=4', image_url='/static/images/f1.png')],
        confidence_detail={'text': 0.9, 'layout': 0.8, 'formula': 0.7}
    )

    data = candidate.to_dict()
    assert data['content'] == '求 x^2=4 的解。'
    assert data['formula_latex'] == ['x^2=4']
    assert data['formula_images'] == ['/static/images/f1.png']
    assert data['images'][0]['type'] == 'diagram'
    assert data['confidence'] == 0.8
