"""Seed question loader. Idempotent: skips questions whose (subject, content) already exists."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_seed_questions(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_questions(items):
    """Import questions, skipping ones already present (by subject+content)."""
    from models import db, Question
    created = 0
    for item in items:
        existing = Question.query.filter_by(
            subject=item['subject'], content=item['content']
        ).first()
        if existing:
            continue
        q = Question(**item)
        db.session.add(q)
        created += 1
    db.session.commit()
    return created


def main():
    from app import app
    seed_path = os.path.join(os.path.dirname(__file__), 'seeds', 'questions_seed.json')
    items = load_seed_questions(seed_path)
    with app.app_context():
        created = import_questions(items)
    print(f"Seeded {created} new questions (of {len(items)} in file)")


if __name__ == '__main__':
    main()
