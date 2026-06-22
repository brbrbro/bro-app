import json
from datetime import datetime, timezone
from flask import jsonify, request
from sqlalchemy import func
from models import db, ImportBatch, ParsedQuestion, Question
from . import admin_bp


def _parse_date(value):
    if not value:
        return None
    return datetime.fromisoformat(value)


def _batch_to_dict(batch):
    low_confidence_count = ParsedQuestion.query.filter(
        ParsedQuestion.batch_id == batch.id,
        ParsedQuestion.confidence < 0.85
    ).count()
    parsed = batch.parsed_questions or 0
    approved = batch.approved_questions or 0
    success_rate = round(approved / parsed, 3) if parsed else 0
    return {
        'id': batch.id,
        'source_type': batch.source_type,
        'source_file': batch.source_file,
        'status': batch.status,
        'exam_type': batch.exam_type,
        'subject': batch.subject,
        'grade': batch.grade,
        'knowledge_point': batch.knowledge_point,
        'total_questions': batch.total_questions or 0,
        'parsed_questions': parsed,
        'approved_questions': approved,
        'success_rate': success_rate,
        'low_confidence_count': low_confidence_count,
        'created_at': batch.created_at.isoformat() if batch.created_at else '',
        'failure_reason': '解析失败' if batch.status in ('failed', 'error') else ''
    }


@admin_bp.route('/import/batches', methods=['GET'])
def admin_import_batches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    subject = request.args.get('subject')
    source_type = request.args.get('source_type')
    start_date = _parse_date(request.args.get('start_date'))
    end_date = _parse_date(request.args.get('end_date'))

    q = ImportBatch.query
    if status:
        q = q.filter_by(status=status)
    if subject:
        q = q.filter_by(subject=subject)
    if source_type:
        q = q.filter_by(source_type=source_type)
    if start_date:
        q = q.filter(ImportBatch.created_at >= start_date)
    if end_date:
        q = q.filter(ImportBatch.created_at <= end_date)

    pagination = q.order_by(ImportBatch.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'batches': [_batch_to_dict(b) for b in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


def _group_batches(field):
    col = getattr(ImportBatch, field)
    rows = db.session.query(col, func.count(ImportBatch.id)).group_by(col).all()
    return [{'key': key or '未设置', 'count': count} for key, count in rows]


@admin_bp.route('/import/batches/<int:batch_id>', methods=['GET'])
def admin_import_batch_detail(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(_batch_to_dict(batch))


@admin_bp.route('/import/batches/<int:batch_id>', methods=['DELETE'])
def admin_delete_import_batch(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    ParsedQuestion.query.filter_by(batch_id=batch_id).delete(synchronize_session=False)
    db.session.delete(batch)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/import/batches/<int:batch_id>/reparse', methods=['POST'])
def admin_reparse_import_batch(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    if not batch.source_url:
        return jsonify({'error': 'source_file_missing'}), 400
    import os
    if not os.path.exists(batch.source_url):
        return jsonify({'error': 'source_file_missing'}), 400
    return jsonify({'success': False, 'error': 'reparse_requires_worker'}), 400


@admin_bp.route('/import/stats', methods=['GET'])
def admin_import_stats():
    batches = ImportBatch.query.all()
    total_batches = len(batches)
    total_parsed = sum(b.parsed_questions or 0 for b in batches)
    total_approved = sum(b.approved_questions or 0 for b in batches)
    failed_batches = sum(1 for b in batches if b.status in ('failed', 'error'))
    avg_questions = round(total_parsed / total_batches, 2) if total_batches else 0

    confidences = [p.confidence for p in ParsedQuestion.query.all() if p.confidence is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0
    low_confidence = ParsedQuestion.query.filter(ParsedQuestion.confidence < 0.85).count()

    return jsonify({
        'totals': {
            'batches': total_batches,
            'parsed_questions': total_parsed,
            'approved_questions': total_approved,
            'approval_rate': round(total_approved / total_parsed, 3) if total_parsed else 0,
            'average_confidence': avg_confidence,
            'low_confidence_count': low_confidence,
            'failed_batches': failed_batches,
            'average_questions_per_batch': avg_questions
        },
        'by_status': _group_batches('status'),
        'by_subject': _group_batches('subject'),
        'by_source_type': _group_batches('source_type')
    })
