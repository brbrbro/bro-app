from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserProgress, Share
from . import sync_bp

@sync_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_sync():
    user_id = get_jwt_identity()
    data = request.get_json()
    for p in data.get('progress', []):
        progress = UserProgress(user_id=user_id, question_id=p.get('question_id'), user_answer=p.get('user_answer'), is_correct=p.get('is_correct'), time_spent=p.get('time_spent', 0))
        db.session.add(progress)
    for n in data.get('notes', []):
        share = Share(user_id=user_id, question_id=n.get('question_id'), type='note', content=n.get('content'), images=n.get('images'))
        db.session.add(share)
    db.session.commit()
    return jsonify({'success': True, 'synced_count': len(data.get('progress', [])) + len(data.get('notes', []))})

@sync_bp.route('/download', methods=['GET'])
@jwt_required()
def download_sync():
    user_id = get_jwt_identity()
    progress = UserProgress.query.filter_by(user_id=user_id).all()
    shares = Share.query.filter_by(user_id=user_id, type='note').all()
    return jsonify({'success': True, 'progress': [{'question_id': p.question_id, 'user_answer': p.user_answer, 'is_correct': p.is_correct, 'answered_at': p.answered_at.timestamp() * 1000} for p in progress], 'notes': [{'id': s.id, 'question_id': s.question_id, 'content': s.content, 'created_at': s.created_at.timestamp() * 1000} for s in shares]})