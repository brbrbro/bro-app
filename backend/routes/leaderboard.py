from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from sqlalchemy import func, Integer
from models import db, User, UserProgress
from . import leaderboard_bp


def _cutoff_for(period):
    if period == 'week':
        return datetime.now(timezone.utc) - timedelta(days=7)
    if period == 'month':
        return datetime.now(timezone.utc) - timedelta(days=30)
    return None


@leaderboard_bp.route('', methods=['GET'])
def get_leaderboard():
    limit = request.args.get('limit', 50, type=int)
    metric = request.args.get('metric', 'correct')
    period = request.args.get('period', 'all')

    cutoff = _cutoff_for(period)

    if metric == 'total':
        score_col = func.count(UserProgress.id)
    else:
        score_col = func.sum(func.cast(UserProgress.is_correct, Integer))

    q = db.session.query(
        User.id, User.nickname, User.avatar, score_col.label('score')
    ).join(UserProgress, UserProgress.user_id == User.id)

    if cutoff:
        q = q.filter(UserProgress.answered_at >= cutoff)

    rows = q.group_by(User.id).order_by(score_col.desc()).limit(limit).all()

    return jsonify({
        'metric': metric,
        'period': period,
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
