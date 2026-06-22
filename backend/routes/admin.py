import importlib
import json
import os
from datetime import datetime, timezone
from flask import jsonify, request
from sqlalchemy import func
from models import db, ImportBatch, ParsedQuestion, Question
from services.document_ingestor import DocumentIngestor
from services.recognition_pipeline import RecognitionPipeline
from services.question_normalizer import QuestionNormalizer
from . import admin_bp

_parsed_from_payload = importlib.import_module('routes.import')._parsed_from_payload


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


def _group_batches(field, query=None):
    col = getattr(ImportBatch, field)
    query = query or ImportBatch.query
    rows = query.with_entities(col, func.count(ImportBatch.id)).group_by(col).all()
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
    if not batch.source_url or not os.path.exists(batch.source_url):
        return jsonify({'error': 'source_file_missing'}), 400

    pages = DocumentIngestor().ingest(batch.source_url, batch.source_type)
    candidates = RecognitionPipeline().recognize(pages, subject=batch.subject or '')
    normalizer = QuestionNormalizer()
    defaults = {
        'exam_type': batch.exam_type or '',
        'subject': batch.subject or '',
        'grade': batch.grade or '',
        'knowledge_point': batch.knowledge_point or '不详'
    }

    ParsedQuestion.query.filter_by(batch_id=batch.id).delete(synchronize_session=False)
    parsed_items = []
    for candidate in candidates:
        payload = normalizer.to_parsed_payload(candidate, defaults)
        parsed = _parsed_from_payload(batch.id, payload)
        db.session.add(parsed)
        parsed_items.append(parsed)

    batch.status = 'reviewing'
    batch.total_questions = len(parsed_items)
    batch.parsed_questions = len(parsed_items)
    batch.approved_questions = 0
    batch.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({'success': True, 'batch_id': batch.id, 'total_questions': len(parsed_items)})


def _question_to_dict(q):
    return {
        'id': q.id,
        'region': q.region,
        'subject': q.subject,
        'grade': q.grade,
        'syllabus': q.syllabus,
        'knowledge_point': q.knowledge_point,
        'type': q.type,
        'difficulty': q.difficulty,
        'content': q.content,
        'answer': q.answer,
        'explanation': q.explanation,
        'options': json.loads(q.options) if q.options else [],
        'solved_count': q.solved_count or 0,
        'correct_rate': q.correct_rate or 0,
        'source': q.source,
        'status': q.status,
        'created_at': q.created_at.isoformat() if q.created_at else ''
    }


@admin_bp.route('/questions', methods=['GET'])
def admin_questions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword')
    subject = request.args.get('subject')
    status = request.args.get('status')
    grade = request.args.get('grade')
    knowledge_point = request.args.get('knowledge_point')
    question_type = request.args.get('type')
    difficulty = request.args.get('difficulty', type=int)
    source = request.args.get('source')
    q = Question.query
    if keyword:
        q = q.filter(Question.content.contains(keyword))
    if subject:
        q = q.filter_by(subject=subject)
    if status:
        q = q.filter_by(status=status)
    if grade:
        q = q.filter_by(grade=grade)
    if knowledge_point:
        q = q.filter_by(knowledge_point=knowledge_point)
    if question_type:
        q = q.filter_by(type=question_type)
    if difficulty is not None:
        q = q.filter_by(difficulty=difficulty)
    if source:
        q = q.filter_by(source=source)
    pagination = q.order_by(Question.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'questions': [_question_to_dict(question) for question in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@admin_bp.route('/questions/<int:question_id>', methods=['GET'])
def admin_question_detail(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({'question': _question_to_dict(q)})


@admin_bp.route('/questions/<int:question_id>', methods=['PUT'])
def admin_update_question(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    data = request.get_json() or {}
    for field in ('region', 'subject', 'grade', 'syllabus', 'knowledge_point', 'type', 'difficulty', 'content', 'answer', 'explanation', 'source', 'status'):
        if field in data:
            setattr(q, field, data[field])
    if 'options' in data:
        q.options = json.dumps(data['options'], ensure_ascii=False)
    db.session.commit()
    return jsonify({'question': _question_to_dict(q)})


@admin_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def admin_delete_question(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    db.session.delete(q)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/questions/<int:question_id>/archive', methods=['POST'])
def admin_archive_question(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    q.status = 'archived'
    db.session.commit()
    return jsonify({'question': _question_to_dict(q)})


def _issue(issue_type, question, severity, suggestion):
    return {
        'issue_type': issue_type,
        'severity': severity,
        'question_id': question.id,
        'content': question.content,
        'subject': question.subject,
        'suggestion': suggestion,
        'status': question.status
    }


@admin_bp.route('/quality/issues', methods=['GET'])
def admin_quality_issues():
    issue_type = request.args.get('issue_type')
    severity = request.args.get('severity')
    subject = request.args.get('subject')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    issues = []
    valid_types = {'choice', 'blank', 'comprehensive'}

    for q in Question.query.all():
        if not q.answer:
            issues.append(_issue('missing_answer', q, 'high', 'Add an answer'))
        if not q.explanation:
            issues.append(_issue('missing_explanation', q, 'medium', 'Add an explanation'))
        if q.type == 'choice':
            try:
                options = json.loads(q.options) if q.options else []
                if not isinstance(options, list) or len(options) < 2:
                    issues.append(_issue('invalid_options', q, 'high', 'Provide at least two options'))
            except json.JSONDecodeError:
                issues.append(_issue('invalid_options', q, 'high', 'Store options as a valid JSON list'))
        if q.type not in valid_types:
            issues.append(_issue('unknown_type', q, 'medium', 'Use choice, blank, or comprehensive'))
        if not q.subject or not q.grade or not q.knowledge_point:
            issues.append(_issue('missing_taxonomy', q, 'medium', 'Fill subject, grade, and knowledge point'))

    duplicates = db.session.query(Question.content).group_by(Question.content).having(func.count(Question.id) > 1).all()
    for (content,) in duplicates:
        q = Question.query.filter_by(content=content).first()
        issues.append(_issue('duplicate_content', q, 'medium', 'Merge or remove duplicate content'))

    for p in ParsedQuestion.query.filter(ParsedQuestion.status == 'pending', ParsedQuestion.confidence < 0.85).all():
        issues.append({
            'issue_type': 'low_confidence_import',
            'severity': 'medium',
            'parsed_question_id': p.id,
            'batch_id': p.batch_id,
            'content': p.content,
            'subject': p.subject,
            'confidence': p.confidence,
            'suggestion': 'Review imported question manually'
        })

    if issue_type:
        issues = [item for item in issues if item['issue_type'] == issue_type]
    if severity:
        issues = [item for item in issues if item.get('severity') == severity]
    if subject:
        issues = [item for item in issues if item.get('subject') == subject]

    total = len(issues)
    pages = (total + per_page - 1) // per_page if per_page else 0
    start = (page - 1) * per_page
    end = start + per_page
    return jsonify({'issues': issues[start:end], 'total': total, 'page': page, 'pages': pages})


@admin_bp.route('/import/stats', methods=['GET'])
def admin_import_stats():
    start_date = _parse_date(request.args.get('start_date') or request.args.get('start'))
    end_date = _parse_date(request.args.get('end_date') or request.args.get('end'))
    group_by = request.args.get('group_by')
    batch_query = ImportBatch.query
    if start_date:
        batch_query = batch_query.filter(ImportBatch.created_at >= start_date)
    if end_date:
        batch_query = batch_query.filter(ImportBatch.created_at <= end_date)

    batches = batch_query.all()
    batch_ids = [b.id for b in batches]
    total_batches = len(batches)
    total_parsed = sum(b.parsed_questions or 0 for b in batches)
    total_approved = sum(b.approved_questions or 0 for b in batches)
    failed_batches = sum(1 for b in batches if b.status in ('failed', 'error'))
    avg_questions = round(total_parsed / total_batches, 2) if total_batches else 0

    parsed_query = ParsedQuestion.query
    if batch_ids:
        parsed_query = parsed_query.filter(ParsedQuestion.batch_id.in_(batch_ids))
    elif start_date or end_date:
        parsed_query = parsed_query.filter(False)
    confidences = [p.confidence for p in parsed_query.all() if p.confidence is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0
    low_confidence = parsed_query.filter(ParsedQuestion.confidence < 0.85).count()

    if group_by in ('status', 'subject', 'source_type'):
        grouped = _group_batches(group_by, batch_query)
    elif group_by == 'day':
        counts = {}
        for batch in batches:
            if batch.created_at:
                key = batch.created_at.date().isoformat()
                counts[key] = counts.get(key, 0) + 1
        grouped = [{'key': key, 'count': counts[key]} for key in sorted(counts)]
    else:
        grouped = []

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
        'by_status': _group_batches('status', batch_query),
        'by_subject': _group_batches('subject', batch_query),
        'by_source_type': _group_batches('source_type', batch_query),
        'grouped': grouped
    })
