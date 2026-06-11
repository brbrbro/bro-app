from datetime import date, timedelta
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, DailyCheckIn
from . import checkin_bp


@checkin_bp.route('/today', methods=['GET'])
@jwt_required()
def today_status():
    user_id = int(get_jwt_identity())
    today = date.today()
    record = DailyCheckIn.query.filter_by(user_id=user_id, check_date=today).first()
    user = db.session.get(User, user_id)
    return jsonify({
        'already_checked': record is not None,
        'today': today.isoformat(),
        'points': user.points if user else 0,
        'streak': record.streak if record else 0
    })


@checkin_bp.route('', methods=['POST'])
@jwt_required()
def do_checkin():
    user_id = int(get_jwt_identity())
    today = date.today()

    existing = DailyCheckIn.query.filter_by(user_id=user_id, check_date=today).first()
    if existing:
        user = db.session.get(User, user_id)
        return jsonify({
            'success': False,
            'error': 'already_checked',
            'points': user.points,
            'streak': existing.streak
        }), 409

    yesterday = today - timedelta(days=1)
    last = DailyCheckIn.query.filter_by(user_id=user_id, check_date=yesterday).first()
    streak = (last.streak + 1) if last else 1

    points_award = 10 + min(streak, 7) * 2
    exp_award = 5 + min(streak, 7)

    record = DailyCheckIn(
        user_id=user_id, check_date=today,
        points_awarded=points_award, exp_awarded=exp_award, streak=streak
    )
    db.session.add(record)

    user = db.session.get(User, user_id)
    user.points = (user.points or 0) + points_award
    user.exp = (user.exp or 0) + exp_award
    while user.exp >= 100:
        user.exp -= 100
        user.level += 1

    db.session.commit()
    return jsonify({
        'success': True,
        'points_awarded': points_award,
        'exp_awarded': exp_award,
        'streak': streak,
        'total_points': user.points,
        'level': user.level,
        'exp': user.exp
    })


@checkin_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    records = DailyCheckIn.query.filter_by(user_id=user_id) \
        .order_by(DailyCheckIn.check_date.desc()).limit(30).all()
    return jsonify({
        'records': [{
            'date': r.check_date.isoformat(),
            'points': r.points_awarded,
            'exp': r.exp_awarded,
            'streak': r.streak
        } for r in records]
    })
