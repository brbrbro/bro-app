from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Share
from . import shares_bp

@shares_bp.route('', methods=['GET'])
def get_shares():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    question_id = request.args.get('question_id', type=int)
    share_type = request.args.get('type')
    query = Share.query.filter_by(status='approved')
    if question_id: query = query.filter_by(question_id=question_id)
    if share_type: query = query.filter_by(type=share_type)
    pagination = query.order_by(Share.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({'shares': [{'id': s.id, 'user_nickname': s.user.nickname if s.user else '匿名用户', 'user_avatar': s.user.avatar if s.user else '', 'question_id': s.question_id, 'type': s.type, 'content': s.content, 'images': s.images, 'like_count': s.like_count, 'comment_count': s.comment_count, 'created_at': s.created_at.isoformat()} for s in pagination.items], 'total': pagination.total})

@shares_bp.route('', methods=['POST'])
@jwt_required()
def create_share():
    user_id = get_jwt_identity()
    data = request.get_json()
    share = Share(user_id=user_id, question_id=data.get('question_id'), type=data.get('type', 'note'), content=data.get('content'), images=data.get('images'), status='approved')
    db.session.add(share)
    db.session.commit()
    return jsonify({'success': True, 'share_id': share.id}), 201

@shares_bp.route('/<int:share_id>/like', methods=['POST'])
@jwt_required()
def like_share(share_id):
    share = Share.query.get_or_404(share_id)
    share.like_count += 1
    db.session.commit()
    return jsonify({'success': True, 'like_count': share.like_count})