import os
import json
from flask import request, jsonify
from werkzeug.utils import secure_filename
from models import db, ImportBatch, ParsedQuestion, Question
from services.file_processor import FileProcessor
from services.ai_parser import AIParser
from . import import_bp

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    batch = ImportBatch.query.get_or_404(batch_id)
    
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
        'completed_at': batch.completed_at.isoformat() if batch.completed_at else None
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

@import_bp.route('/batch/<int:batch_id>/questions', methods=['GET'])
def get_batch_questions(batch_id):
    status = request.args.get('status', 'pending')
    
    questions = ParsedQuestion.query.filter_by(
        batch_id=batch_id,
        status=status
    ).all()
    
    return jsonify({
        'questions': [{
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
            'status': q.status
        } for q in questions]
    })

@import_bp.route('/question/<int:question_id>/approve', methods=['POST'])
def approve_question(question_id):
    data = request.get_json()
    
    parsed = ParsedQuestion.query.get_or_404(question_id)
    
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
    
    batch = ImportBatch.query.get(parsed.batch_id)
    if batch:
        batch.approved_questions += 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'question_id': question.id})

@import_bp.route('/question/<int:question_id>/reject', methods=['POST'])
def reject_question(question_id):
    data = request.get_json()
    
    parsed = ParsedQuestion.query.get_or_404(question_id)
    parsed.status = 'rejected'
    parsed.review_notes = data.get('notes', '')
    
    db.session.commit()
    
    return jsonify({'success': True})
