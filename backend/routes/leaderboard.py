from flask import request, jsonify
from sqlalchemy import func, Integer
from models import db, User, UserProgress
from . import leaderboard_bp


@leaderboard_bp.route('', methods=['GET'])
def get_leaderboard():
    limit = request.args.get('limit', 50, type=int)
    metric = request.args.get('metric', 'correct')

    if metric == 'total':
        rows = db.session.query(
            User.id, User.nickname, User.avatar,
            func.count(UserProgress.id).label('score')
        ).join(UserProgress, UserProgress.user_id == User.id) \
         .group_by(User.id).order_by(func.count(UserProgress.id).desc()).limit(limit).all()
    else:
        rows = db.session.query(
            User.id, User.nickname, User.avatar,
            func.sum(func.cast(UserProgress.is_correct, Integer)).label('score')
        ).join(UserProgress, UserProgress.user_id == User.id) \
         .group_by(User.id).order_by(func.sum(func.cast(UserProgress.is_correct, Integer)).desc()).limit(limit).all()

    return jsonify({
        'metric': metric,
        'ranking': [
            {
                'rank': i + 1,
                'user_id': r.id,
                'nickname': r.nickname or '匿名',
                'avatar': r.avatar or '',
                'score': int(r.score or 0)
            }
            for i, r in enumerate(rows)
        ]
    })
