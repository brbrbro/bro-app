from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import or_
from models import db, Notification
from . import notification_bp


@notification_bp.route('', methods=['GET'])
def list_notifications():
    """List notifications: system-wide (user_id NULL) + user-specific if authenticated."""
    try:
        verify_jwt_in_request(optional=True)
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str) if user_id_str else None
    except Exception:
        user_id = None

    q = Notification.query
    if user_id:
        q = q.filter(or_(Notification.user_id.is_(None), Notification.user_id == user_id))
    else:
        q = q.filter(Notification.user_id.is_(None))
    items = q.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify({
        'notifications': [{
            'id': n.id, 'type': n.type, 'title': n.title, 'content': n.content,
            'read': bool(n.read), 'created_at': n.created_at.isoformat() if n.created_at else ''
        } for n in items]
    })


@notification_bp.route('/<int:nid>/read', methods=['POST'])
@jwt_required()
def mark_read(nid):
    n = db.session.get(Notification, nid)
    if not n:
        return jsonify({'error': 'not_found'}), 404
    n.read = True
    db.session.commit()
    return jsonify({'success': True})


@notification_bp.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter(
        or_(Notification.user_id.is_(None), Notification.user_id == user_id)
    ).update({'read': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})
