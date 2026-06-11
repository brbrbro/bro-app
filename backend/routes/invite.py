from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Invitation
from . import invite_bp


def parse_invite_code(code):
    """BRO000123 -> 123. Returns None if invalid."""
    if not code or not code.startswith('BRO'):
        return None
    try:
        return int(code[3:])
    except ValueError:
        return None


@invite_bp.route('/bind', methods=['POST'])
@jwt_required()
def bind():
    invitee_id = int(get_jwt_identity())
    data = request.get_json() or {}
    code = data.get('invite_code', '')

    inviter_id = parse_invite_code(code)
    if not inviter_id:
        return jsonify({'error': 'invalid_code'}), 400

    if inviter_id == invitee_id:
        return jsonify({'error': 'cannot_invite_self'}), 400

    inviter = db.session.get(User, inviter_id)
    if not inviter:
        return jsonify({'error': 'inviter_not_found'}), 404

    existing = Invitation.query.filter_by(invitee_id=invitee_id).first()
    if existing:
        return jsonify({'error': 'already_bound', 'inviter_id': existing.inviter_id}), 409

    inv = Invitation(inviter_id=inviter_id, invitee_id=invitee_id, invite_code=code, points_awarded=50)
    db.session.add(inv)

    inviter.points = (inviter.points or 0) + 50
    invitee = db.session.get(User, invitee_id)
    invitee.points = (invitee.points or 0) + 50

    db.session.commit()
    return jsonify({
        'success': True,
        'inviter_id': inviter_id,
        'points_awarded_each': 50
    })


@invite_bp.route('/list', methods=['GET'])
@jwt_required()
def list_invitees():
    inviter_id = int(get_jwt_identity())
    invs = Invitation.query.filter_by(inviter_id=inviter_id).all()
    invitees = []
    for inv in invs:
        u = db.session.get(User, inv.invitee_id)
        if u:
            invitees.append({
                'user_id': u.id,
                'nickname': u.nickname,
                'avatar': u.avatar,
                'invited_at': inv.created_at.isoformat()
            })
    return jsonify({'invitees': invitees, 'total': len(invitees)})
