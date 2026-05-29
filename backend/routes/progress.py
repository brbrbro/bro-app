from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, UserProgress, Question
from . import progress_bp

@progress_bp.route('', methods=['POST'])
@jwt_required()
def submit_progress():
    """提交答题记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('question_id'):
        return jsonify({'error': '缺少 question_id'}), 400
    
    question = Question.query.get(data['question_id'])
    if not question:
        return jsonify({'error': '题目不存在'}), 404
    
    progress = UserProgress(
        user_id=user_id,
        question_id=data['question_id'],
        user_answer=data.get('user_answer', ''),
        is_correct=data.get('is_correct', False),
        time_spent=data.get('time_spent', 0)
    )
    db.session.add(progress)
    
    question.solved_count += 1
    db.session.commit()
    
    return jsonify({'success': True, 'progress_id': progress.id})

@progress_bp.route('', methods=['GET'])
@jwt_required()
def get_progress():
    """获取用户答题记录"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = UserProgress.query.filter_by(user_id=user_id)
    pagination = query.order_by(UserProgress.answered_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'progress': [{
            'id': p.id,
            'question_id': p.question_id,
            'user_answer': p.user_answer,
            'is_correct': p.is_correct,
            'time_spent': p.time_spent,
            'answered_at': p.answered_at.isoformat()
        } for p in pagination.items],
        'total': pagination.total
    })

@progress_bp.route('/wrong', methods=['GET'])
@jwt_required()
def get_wrong_questions():
    """获取错题本"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    wrong_progress = UserProgress.query.filter_by(
        user_id=user_id, is_correct=False
    ).order_by(UserProgress.answered_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'wrong_questions': [{
            'id': p.id,
            'question_id': p.question_id,
            'user_answer': p.user_answer,
            'answered_at': p.answered_at.isoformat()
        } for p in wrong_progress.items],
        'total': wrong_progress.total
    })

@progress_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """获取用户学习统计"""
    user_id = get_jwt_identity()
    
    total = UserProgress.query.filter_by(user_id=user_id).count()
    correct = UserProgress.query.filter_by(user_id=user_id, is_correct=True).count()
    wrong = UserProgress.query.filter_by(user_id=user_id, is_correct=False).count()
    
    return jsonify({
        'total_answered': total,
        'correct_count': correct,
        'wrong_count': wrong,
        'correct_rate': round(correct / total * 100, 1) if total > 0 else 0
    })
