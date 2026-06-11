import json
from seed_questions import load_seed_questions, import_questions

SAMPLE = [
    {
        "region": "mainland", "subject": "数学", "grade": "高一",
        "type": "choice", "difficulty": 1, "content": "1+1=?",
        "answer": "2", "explanation": "", "options": "[]",
        "source": "seed", "status": "approved", "syllabus": "", "knowledge_point": ""
    }
]


def test_load_seed_questions_returns_list(tmp_path):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(SAMPLE), encoding='utf-8')
    items = load_seed_questions(str(path))
    assert len(items) == 1
    assert items[0]['subject'] == '数学'


def test_import_questions_creates_rows(client, app):
    from models import Question
    with app.app_context():
        created = import_questions(SAMPLE)
        assert created == 1
        assert Question.query.count() == 1


def test_import_questions_skips_duplicates(client, app):
    from models import Question
    with app.app_context():
        import_questions(SAMPLE)
        created = import_questions(SAMPLE)
        assert created == 0
        assert Question.query.count() == 1
