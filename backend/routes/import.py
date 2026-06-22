import os
import json
from flask import request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, ImportBatch, ParsedQuestion, Question
from services.file_processor import FileProcessor
from services.ai_parser import AIParser
from services.document_ingestor import DocumentIngestor
from services.recognition_pipeline import RecognitionPipeline
from services.question_normalizer import QuestionNormalizer
from . import import_bp

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _parsed_from_payload(batch_id, payload):
    return ParsedQuestion(
        batch_id=batch_id,
        raw_content=json.dumps(payload, ensure_ascii=False),
        content=payload.get('content', ''),
        options=json.dumps(payload.get('options', []), ensure_ascii=False),
        answer=payload.get('answer', ''),
        explanation=payload.get('explanation', ''),
        exam_type=payload.get('exam_type', ''),
        subject=payload.get('subject', ''),
        grade=payload.get('grade', ''),
        knowledge_point=payload.get('knowledge_point', '不详'),
        type=payload.get('type', 'unknown'),
        difficulty=payload.get('difficulty', 3),
        confidence=payload.get('confidence', 0),
        status='pending',
        source_page=payload.get('source_page'),
        bbox=json.dumps(payload.get('bbox'), ensure_ascii=False),
        images=json.dumps(payload.get('images', []), ensure_ascii=False),
        formula_latex=json.dumps(payload.get('formula_latex', []), ensure_ascii=False),
        formula_images=json.dumps(payload.get('formula_images', []), ensure_ascii=False),
        raw_ocr_text=payload.get('raw_ocr_text', ''),
        confidence_detail=json.dumps(payload.get('confidence_detail', {}), ensure_ascii=False)
    )


def _serialize_parsed_question(q):
    return {
        'id': q.id,
        'content': q.content,
        'options': json.loads(q.options) if q.options else [],
        'answer': q.answer,
        'explanation': q.explanation,
        'exam_type': q.exam_type,
        'subject': q.subject,
        'grade': q.grade,
        'knowledge_point': q.knowledge_point,
        'type': q.type,
        'difficulty': q.difficulty,
        'confidence': q.confidence,
        'status': q.status,
        'source_page': q.source_page,
        'bbox': json.loads(q.bbox) if q.bbox else None,
        'images': json.loads(q.images) if q.images else [],
        'formula_latex': json.loads(q.formula_latex) if q.formula_latex else [],
        'formula_images': json.loads(q.formula_images) if q.formula_images else [],
        'raw_ocr_text': q.raw_ocr_text,
        'confidence_detail': json.loads(q.confidence_detail) if q.confidence_detail else {}
    }


@import_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    # Get form data
    exam_type = request.form.get('exam_type', '')
    subject = request.form.get('subject', '')
    grade = request.form.get('grade', '')
    knowledge_point = request.form.get('knowledge_point', '不详')
    created_by = request.form.get('created_by', 'admin')
    
    # Validate required fields
    if not exam_type:
        return jsonify({'error': '请选择考试体系'}), 400
    if not subject:
        return jsonify({'error': '请选择科目'}), 400
    
    processor = FileProcessor()
    filename = secure_filename(file.filename)
    file_path = processor.save_upload(file, filename)
    file_type = filename.rsplit('.', 1)[1].lower()
    
    batch = ImportBatch(
        source_type=file_type,
        source_file=filename,
        source_url=file_path,
        status='processing',
        exam_type=exam_type,
        subject=subject,
        grade=grade,
        knowledge_point=knowledge_point,
        created_by=created_by
    )
    db.session.add(batch)
    db.session.commit()
    
    try:
        result = processor.process_file(file_path, file_type)
        
        ai_parser = AIParser()
        questions = ai_parser.batch_parse(result, subject)
        
        for q_data in questions:
            parsed = ParsedQuestion(
                batch_id=batch.id,
                raw_content=json.dumps(q_data),
                content=q_data.get('content', ''),
                options=json.dumps(q_data.get('options', [])),
                answer=q_data.get('answer', ''),
                explanation=q_data.get('explanation', ''),
                exam_type=exam_type,
                subject=subject,
                grade=grade,
                knowledge_point=knowledge_point,
                type=q_data.get('type', 'unknown'),
                difficulty=q_data.get('difficulty', 3),
                confidence=0.8,
                status='pending'
            )
            db.session.add(parsed)
        
        batch.status = 'reviewing'
        batch.parsed_questions = len(questions)
        batch.total_questions = len(questions)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'batch_id': batch.id,
            'total_questions': len(questions),
            'message': f'成功解析 {len(questions)} 道题目，等待审核'
        })
        
    except Exception as e:
        batch.status = 'error'
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@import_bp.route('/status/<int:batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        abort(404)
    completed_at = getattr(batch, 'completed_at', None)
    
    return jsonify({
        'id': batch.id,
        'status': batch.status,
        'source_type': batch.source_type,
        'source_file': batch.source_file,
        'exam_type': batch.exam_type,
        'subject': batch.subject,
        'grade': batch.grade,
        'knowledge_point': batch.knowledge_point,
        'total_questions': batch.total_questions,
        'parsed_questions': batch.parsed_questions,
        'approved_questions': batch.approved_questions,
        'created_at': batch.created_at.isoformat(),
        'completed_at': completed_at.isoformat() if completed_at else None
    })

@import_bp.route('/batches', methods=['GET'])
def get_batches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    batches = ImportBatch.query.order_by(ImportBatch.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'batches': [{
            'id': b.id,
            'source_type': b.source_type,
            'source_file': b.source_file,
            'status': b.status,
            'exam_type': b.exam_type,
            'subject': b.subject,
            'grade': b.grade,
            'knowledge_point': b.knowledge_point,
            'total_questions': b.total_questions,
            'parsed_questions': b.parsed_questions,
            'approved_questions': b.approved_questions,
            'created_at': b.created_at.isoformat()
        } for b in batches.items],
        'total': batches.total
    })

@import_bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_batch_detail(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        abort(404)
    completed_at = getattr(batch, 'completed_at', None)
    return jsonify({
        'id': batch.id,
        'status': batch.status,
        'source_type': batch.source_type,
        'source_file': batch.source_file,
        'exam_type': batch.exam_type,
        'subject': batch.subject,
        'grade': batch.grade,
        'knowledge_point': batch.knowledge_point,
        'total_questions': batch.total_questions,
        'parsed_questions': batch.parsed_questions,
        'approved_questions': batch.approved_questions,
        'created_at': batch.created_at.isoformat(),
        'completed_at': completed_at.isoformat() if completed_at else None
    })


@import_bp.route('/batch/<int:batch_id>/questions', methods=['GET'])
def get_batch_questions(batch_id):
    status = request.args.get('status', 'pending')
    
    questions = ParsedQuestion.query.filter_by(
        batch_id=batch_id,
        status=status
    ).all()
    
    return jsonify({
        'questions': [_serialize_parsed_question(q) for q in questions]
    })

@import_bp.route('/question/<int:question_id>/approve', methods=['POST'])
def approve_question(question_id):
    data = request.get_json()
    
    parsed = db.session.get(ParsedQuestion, question_id)
    if not parsed:
        abort(404)
    
    parsed.content = data.get('content', parsed.content)
    parsed.options = json.dumps(data.get('options', []))
    parsed.answer = data.get('answer', parsed.answer)
    parsed.explanation = data.get('explanation', parsed.explanation)
    parsed.subject = data.get('subject', parsed.subject)
    parsed.grade = data.get('grade', parsed.grade)
    parsed.knowledge_point = data.get('knowledge_point', parsed.knowledge_point)
    parsed.type = data.get('type', parsed.type)
    parsed.difficulty = data.get('difficulty', parsed.difficulty)
    parsed.status = 'approved'
    
    question = Question(
        region=data.get('region', 'mainland'),
        subject=parsed.subject,
        grade=parsed.grade,
        knowledge_point=parsed.knowledge_point,
        type=parsed.type,
        difficulty=parsed.difficulty,
        content=parsed.content,
        answer=parsed.answer,
        explanation=parsed.explanation,
        options=parsed.options,
        source='import',
        status='approved'
    )
    db.session.add(question)
    
    batch = db.session.get(ImportBatch, parsed.batch_id)
    if batch:
        batch.approved_questions = (batch.approved_questions or 0) + 1
        remaining = ParsedQuestion.query.filter_by(batch_id=batch.id, status='pending').count()
        if remaining == 0:
            batch.status = 'completed'
    
    db.session.commit()
    
    return jsonify({'success': True, 'question_id': question.id})

@import_bp.route('/question/<int:question_id>/reject', methods=['POST'])
def reject_question(question_id):
    data = request.get_json()
    
    parsed = db.session.get(ParsedQuestion, question_id)
    if not parsed:
        abort(404)
    parsed.status = 'rejected'
    parsed.review_notes = data.get('notes', '')
    
    db.session.commit()
    
    return jsonify({'success': True})

@import_bp.route('/single', methods=['POST'])
def import_single():
    data = request.get_json() or {}
    text = data.get('text', '')
    exam_type = data.get('exam_type', '')
    subject = data.get('subject', '')
    grade = data.get('grade', '')
    knowledge_point = data.get('knowledge_point', '不详')

    if not exam_type:
        return jsonify({'error': '请选择考试体系'}), 400
    if not subject:
        return jsonify({'error': '请选择科目'}), 400
    if not text.strip():
        return jsonify({'error': '请输入题目内容'}), 400

    from services.import_schema import DocumentPage
    pages = [DocumentPage(page=1, text=text)]
    candidates = RecognitionPipeline().recognize(pages, subject=subject)
    normalizer = QuestionNormalizer()

    batch = ImportBatch(
        source_type='single',
        source_file='single-input',
        source_url='',
        status='reviewing',
        exam_type=exam_type,
        subject=subject,
        grade=grade,
        knowledge_point=knowledge_point,
        created_by=data.get('created_by', 'admin'),
        total_questions=len(candidates),
        parsed_questions=len(candidates)
    )
    db.session.add(batch)
    db.session.commit()

    parsed_items = []
    defaults = {'exam_type': exam_type, 'subject': subject, 'grade': grade, 'knowledge_point': knowledge_point}
    for candidate in candidates:
        payload = normalizer.to_parsed_payload(candidate, defaults)
        parsed = _parsed_from_payload(batch.id, payload)
        db.session.add(parsed)
        parsed_items.append(parsed)

    db.session.commit()

    return jsonify({
        'success': True,
        'batch_id': batch.id,
        'total_questions': len(parsed_items),
        'questions': [_serialize_parsed_question(q) for q in parsed_items]
    })


@import_bp.route('/batch', methods=['POST'])
def import_batch():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400

    exam_type = request.form.get('exam_type', '')
    subject = request.form.get('subject', '')
    grade = request.form.get('grade', '')
    knowledge_point = request.form.get('knowledge_point', '不详')
    if not exam_type:
        return jsonify({'error': '请选择考试体系'}), 400
    if not subject:
        return jsonify({'error': '请选择科目'}), 400

    processor = FileProcessor()
    filename = secure_filename(file.filename)
    file_path = processor.save_upload(file, filename)
    file_type = filename.rsplit('.', 1)[1].lower()

    batch = ImportBatch(
        source_type=file_type,
        source_file=filename,
        source_url=file_path,
        status='processing',
        exam_type=exam_type,
        subject=subject,
        grade=grade,
        knowledge_point=knowledge_point,
        created_by=request.form.get('created_by', 'admin')
    )
    db.session.add(batch)
    db.session.commit()

    try:
        pages = DocumentIngestor().ingest(file_path, file_type)
        candidates = RecognitionPipeline().recognize(pages, subject=subject)
        normalizer = QuestionNormalizer()
        defaults = {'exam_type': exam_type, 'subject': subject, 'grade': grade, 'knowledge_point': knowledge_point}
        parsed_items = []
        for candidate in candidates:
            payload = normalizer.to_parsed_payload(candidate, defaults)
            parsed = _parsed_from_payload(batch.id, payload)
            db.session.add(parsed)
            parsed_items.append(parsed)

        batch.status = 'reviewing'
        batch.total_questions = len(parsed_items)
        batch.parsed_questions = len(parsed_items)
        db.session.commit()

        return jsonify({
            'success': True,
            'batch_id': batch.id,
            'status': batch.status,
            'total_questions': len(parsed_items)
        })
    except Exception as exc:
        batch.status = 'failed'
        db.session.commit()
        return jsonify({'error': str(exc), 'batch_id': batch.id}), 500


@import_bp.route('/my-questions', methods=['GET'])
@jwt_required()
def my_questions():
    status = request.args.get('status', '')
    query = ParsedQuestion.query
    if status:
        query = query.filter_by(status=status)
    items = query.order_by(ParsedQuestion.created_at.desc()).limit(50).all()
    return jsonify({
        'questions': [{
            'id': q.id,
            'content': q.content or q.raw_content or '',
            'subject': q.subject,
            'status': q.status,
            'created_at': q.created_at.strftime('%Y-%m-%d %H:%M')
        } for q in items]
    })


@import_bp.route('/parsed/<int:question_id>', methods=['PUT'])
def update_parsed_question(question_id):
    data = request.get_json() or {}
    parsed = db.session.get(ParsedQuestion, question_id)
    if not parsed:
        return jsonify({'error': 'not_found'}), 404

    for field in ['content', 'answer', 'explanation', 'subject', 'grade', 'knowledge_point', 'type', 'difficulty']:
        if field in data:
            setattr(parsed, field, data[field])
    if 'options' in data:
        parsed.options = json.dumps(data.get('options', []), ensure_ascii=False)
    if 'images' in data:
        parsed.images = json.dumps(data.get('images', []), ensure_ascii=False)
    if 'formula_latex' in data:
        parsed.formula_latex = json.dumps(data.get('formula_latex', []), ensure_ascii=False)
    if 'formula_images' in data:
        parsed.formula_images = json.dumps(data.get('formula_images', []), ensure_ascii=False)

    db.session.commit()
    return jsonify({'success': True, 'question': _serialize_parsed_question(parsed)})


@import_bp.route('/parsed/<int:question_id>/split', methods=['POST'])
def split_parsed_question(question_id):
    data = request.get_json() or {}
    parsed = db.session.get(ParsedQuestion, question_id)
    if not parsed:
        return jsonify({'error': 'not_found'}), 404

    first = data.get('first', {})
    second = data.get('second', {})
    parsed.content = first.get('content', parsed.content)
    parsed.answer = first.get('answer', parsed.answer)
    parsed.explanation = first.get('explanation', parsed.explanation)
    if 'options' in first:
        parsed.options = json.dumps(first.get('options', []), ensure_ascii=False)
    if 'type' in first:
        parsed.type = first.get('type')
    if 'difficulty' in first:
        parsed.difficulty = first.get('difficulty')
    if 'source_page' in first:
        parsed.source_page = first.get('source_page')
    if 'bbox' in first:
        parsed.bbox = json.dumps(first.get('bbox'), ensure_ascii=False)
    if 'images' in first:
        parsed.images = json.dumps(first.get('images', []), ensure_ascii=False)
    if 'formula_latex' in first:
        parsed.formula_latex = json.dumps(first.get('formula_latex', []), ensure_ascii=False)
    if 'formula_images' in first:
        parsed.formula_images = json.dumps(first.get('formula_images', []), ensure_ascii=False)
    if 'raw_ocr_text' in first:
        parsed.raw_ocr_text = first.get('raw_ocr_text')
    if 'confidence_detail' in first:
        parsed.confidence_detail = json.dumps(first.get('confidence_detail', {}), ensure_ascii=False)

    created = ParsedQuestion(
        batch_id=parsed.batch_id,
        raw_content=json.dumps(second, ensure_ascii=False),
        content=second.get('content', ''),
        options=json.dumps(second.get('options', []), ensure_ascii=False),
        answer=second.get('answer', ''),
        explanation=second.get('explanation', ''),
        exam_type=parsed.exam_type,
        subject=parsed.subject,
        grade=parsed.grade,
        knowledge_point=parsed.knowledge_point,
        type=second.get('type', parsed.type),
        difficulty=second.get('difficulty', parsed.difficulty),
        confidence=second.get('confidence', parsed.confidence),
        status='pending',
        source_page=second.get('source_page', parsed.source_page),
        bbox=json.dumps(second.get('bbox'), ensure_ascii=False),
        images=json.dumps(second.get('images', []), ensure_ascii=False),
        formula_latex=json.dumps(second.get('formula_latex', []), ensure_ascii=False),
        formula_images=json.dumps(second.get('formula_images', []), ensure_ascii=False),
        raw_ocr_text=second.get('raw_ocr_text', ''),
        confidence_detail=json.dumps(second.get('confidence_detail', {}), ensure_ascii=False)
    )
    db.session.add(created)
    batch = db.session.get(ImportBatch, parsed.batch_id)
    if batch:
        batch.total_questions = (batch.total_questions or 0) + 1
        batch.parsed_questions = (batch.parsed_questions or 0) + 1
    db.session.commit()
    return jsonify({'success': True, 'created_id': created.id, 'updated_id': parsed.id})


@import_bp.route('/parsed/<int:question_id>/merge', methods=['POST'])
def merge_parsed_question(question_id):
    data = request.get_json() or {}
    target_id = data.get('target_id')
    if target_id == question_id:
        return jsonify({'error': 'cannot_merge_self'}), 400
    source = db.session.get(ParsedQuestion, question_id)
    target = db.session.get(ParsedQuestion, target_id)
    if not source or not target:
        return jsonify({'error': 'not_found'}), 404
    if source.batch_id != target.batch_id:
        return jsonify({'error': 'different_batch'}), 400

    target.content = (target.content or '') + '\n' + (source.content or '')
    if source.explanation:
        target.explanation = ((target.explanation or '') + '\n' + source.explanation).strip()
    if source.raw_ocr_text:
        target.raw_ocr_text = ((target.raw_ocr_text or '') + '\n' + source.raw_ocr_text).strip()
    if not target.source_page and source.source_page:
        target.source_page = source.source_page
    if not target.bbox and source.bbox:
        target.bbox = source.bbox
    for field in ['images', 'formula_latex', 'formula_images']:
        target_items = json.loads(getattr(target, field) or '[]')
        source_items = json.loads(getattr(source, field) or '[]')
        setattr(target, field, json.dumps(target_items + source_items, ensure_ascii=False))
    target_conf = json.loads(target.confidence_detail or '{}')
    source_conf = json.loads(source.confidence_detail or '{}')
    for key, value in source_conf.items():
        target_conf[f'merged_{key}'] = value
    target.confidence_detail = json.dumps(target_conf, ensure_ascii=False)
    source.status = 'rejected'
    source.review_notes = f'Merged into ParsedQuestion #{target.id}'
    db.session.commit()
    return jsonify({'success': True, 'target_id': target.id, 'merged_id': source.id})


@import_bp.route('/batch/<int:batch_id>/approve-safe', methods=['POST'])
def approve_safe_questions(batch_id):
    data = request.get_json() or {}
    min_confidence = float(data.get('min_confidence', 0.85))
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    questions = ParsedQuestion.query.filter_by(batch_id=batch_id, status='pending').all()
    approved_count = 0
    for parsed in questions:
        if (parsed.confidence or 0) < min_confidence:
            continue
        question = Question(
            region=data.get('region', 'mainland'),
            subject=parsed.subject,
            grade=parsed.grade,
            knowledge_point=parsed.knowledge_point,
            type=parsed.type,
            difficulty=parsed.difficulty,
            content=parsed.content,
            answer=parsed.answer,
            explanation=parsed.explanation,
            options=parsed.options,
            source='import',
            status='approved'
        )
        db.session.add(question)
        parsed.status = 'approved'
        approved_count += 1

    remaining = ParsedQuestion.query.filter_by(batch_id=batch_id, status='pending').count()
    batch.approved_questions = (batch.approved_questions or 0) + approved_count
    if remaining == 0 and approved_count > 0:
        batch.status = 'completed'
    else:
        batch.status = 'reviewing'

    db.session.commit()
    return jsonify({'success': True, 'approved_count': approved_count})
