from flask import request, jsonify, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from . import users_bp
import hashlib

@users_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or not data.get('openid_hash'):
        return jsonify({'error': '缺少 openid_hash'}), 400
    
    existing = User.query.filter_by(openid_hash=data['openid_hash']).first()
    if existing:
        return jsonify({'error': '用户已存在'}), 409
    
    user = User(
        openid_hash=data['openid_hash'],
        nickname=data.get('nickname', ''),
        avatar=data.get('avatar', ''),
        region=data.get('region', 'mainland')
    )
    db.session.add(user)
    db.session.commit()
    
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'region': user.region
        }
    }), 201

@users_bp.route('/wx-login', methods=['POST'])
def wx_login():
    """微信小程序登录 (Mock version)"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': '缺少 code'}), 400
    
    # Mock: use code hash as openid
    openid_hash = hashlib.sha256(code.encode()).hexdigest()[:32]
    
    user = User.query.filter_by(openid_hash=openid_hash).first()
    if not user:
        user = User(
            openid_hash=openid_hash,
            nickname=f'用户_{openid_hash[:6]}',
            region='mainland'
        )
        db.session.add(user)
        db.session.commit()
    
    token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'region': user.region,
            'member_type': user.member_type,
            'gold': user.gold
        }
    })

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
    return jsonify({
        'id': user.id,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'region': user.region,
        'member_type': user.member_type,
        'gold': user.gold,
        'points': user.points or 0,
        'exp': user.exp or 0,
        'level': user.level or 1,
        'created_at': user.created_at.isoformat()
    })

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
    data = request.get_json()
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'region' in data:
        user.region = data['region']
    
    db.session.commit()
    
    return jsonify({'success': True})
