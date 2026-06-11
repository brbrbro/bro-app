from datetime import datetime, time, timezone
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models import db, StudySession
from . import study_bp


@study_bp.route('/session', methods=['POST'])
@jwt_required()
def submit_session():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    seconds = int(data.get('seconds') or 0)
    if seconds <= 0:
        return jsonify({'error': 'invalid_seconds'}), 400

    s = StudySession(user_id=user_id, seconds=seconds)
    db.session.add(s)
    db.session.commit()
    return jsonify({'success': True, 'session_id': s.id})


@study_bp.route('/today', methods=['GET'])
@jwt_required()
def today_total():
    user_id = int(get_jwt_identity())
    # Today in UTC; for finer locale handling, expand later.
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

    total = db.session.query(func.sum(StudySession.seconds)).filter(
        StudySession.user_id == user_id,
        StudySession.started_at >= today_start
    ).scalar() or 0

    return jsonify({
        'today_seconds': int(total),
        'today_minutes': int(total // 60)
    })
