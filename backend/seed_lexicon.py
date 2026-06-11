"""Seed lexicon loader. Idempotent: skips words whose (word, subject) already exist."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_lexicon(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_lexicon(items):
    from models import db, LexiconWord
    created = 0
    for item in items:
        existing = LexiconWord.query.filter_by(
            word=item['word'], subject=item['subject']
        ).first()
        if existing:
            continue
        w = LexiconWord(**item)
        db.session.add(w)
        created += 1
    db.session.commit()
    return created


def main():
    from app import app
    path = os.path.join(os.path.dirname(__file__), 'seeds', 'lexicon_seed.json')
    items = load_lexicon(path)
    with app.app_context():
        created = import_lexicon(items)
    print(f"Seeded {created} new lexicon words (of {len(items)} in file)")


if __name__ == '__main__':
    main()
