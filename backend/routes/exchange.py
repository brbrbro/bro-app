from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, ExchangeRecord
from . import exchange_bp


SHOP_ITEMS = {
    1: {'name': 'AI 解析 1 次', 'cost': 50},
    2: {'name': '错题 PDF 导出', 'cost': 200},
    3: {'name': '免广告 7 天', 'cost': 500},
    4: {'name': 'Premium 1 月', 'cost': 2000},
    5: {'name': '专属头像框', 'cost': 1000},
    6: {'name': '能量饮料 (虚拟)', 'cost': 30}
}


@exchange_bp.route('/items', methods=['GET'])
def list_items():
    return jsonify({
        'items': [{'id': k, **v} for k, v in SHOP_ITEMS.items()]
    })


@exchange_bp.route('', methods=['POST'])
@jwt_required()
def redeem():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    item_id = data.get('item_id')

    item = SHOP_ITEMS.get(item_id)
    if not item:
        return jsonify({'error': 'invalid_item'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'user_not_found'}), 404

    if (user.points or 0) < item['cost']:
        return jsonify({'error': 'insufficient_points', 'balance': user.points}), 409

    user.points -= item['cost']
    record = ExchangeRecord(user_id=user_id, item_id=item_id, item_name=item['name'], cost=item['cost'])
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'item_name': item['name'],
        'cost_paid': item['cost'],
        'remaining_points': user.points,
        'record_id': record.id
    })


@exchange_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    records = ExchangeRecord.query.filter_by(user_id=user_id) \
        .order_by(ExchangeRecord.created_at.desc()).limit(30).all()
    return jsonify({
        'records': [{
            'id': r.id,
            'item_name': r.item_name,
            'cost': r.cost,
            'created_at': r.created_at.isoformat()
        } for r in records]
    })
