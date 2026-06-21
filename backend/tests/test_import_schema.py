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
