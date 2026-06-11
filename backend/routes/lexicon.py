from flask import jsonify, request
from models import LexiconWord
from . import lexicon_bp


@lexicon_bp.route('', methods=['GET'])
def list_words():
    subject = request.args.get('subject')
    limit = request.args.get('limit', 50, type=int)
    q = LexiconWord.query
    if subject:
        q = q.filter_by(subject=subject)
    words = q.order_by(LexiconWord.id).limit(limit).all()
    return jsonify({
        'words': [{
            'id': w.id,
            'word': w.word,
            'definition': w.definition,
            'example': w.example or '',
            'subject': w.subject
        } for w in words]
    })
