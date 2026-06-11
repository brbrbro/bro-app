from flask import request, jsonify
from models import db, Question
from . import questions_bp

@questions_bp.route('', methods=['GET'])
def get_questions():
    region = request.args.get('region', 'mainland')
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    knowledge_point = request.args.get('knowledge_point')
    difficulty = request.args.get('difficulty', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Question.query.filter_by(status='approved', region=region)
    
    if subject:
        query = query.filter_by(subject=subject)
    if grade:
        query = query.filter_by(grade=grade)
    if knowledge_point:
        query = query.filter_by(knowledge_point=knowledge_point)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'questions': [{
            'id': q.id,
            'subject': q.subject,
            'grade': q.grade,
            'type': q.type,
            'difficulty': q.difficulty,
            'content': q.content,
            'options': q.options
        } for q in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    })

@questions_bp.route('/<int:question_id>', methods=['GET'])
def get_question(question_id):
    question = Question.query.get_or_404(question_id)
    return jsonify({
        'id': question.id,
        'region': question.region,
        'subject': question.subject,
        'grade': question.grade,
        'syllabus': question.syllabus,
        'knowledge_point': question.knowledge_point,
        'type': question.type,
        'difficulty': question.difficulty,
        'content': question.content,
        'answer': question.answer,
        'explanation': question.explanation,
        'options': question.options
    })

@questions_bp.route('/random', methods=['GET'])
def get_random_question():
    region = request.args.get('region', 'mainland')
    subject = request.args.get('subject')
    difficulty = request.args.get('difficulty', type=int)
    
    query = Question.query.filter_by(status='approved', region=region)
    if subject:
        query = query.filter_by(subject=subject)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    question = query.order_by(db.func.random()).first()
    if not question:
        return jsonify({'error': 'No questions found'}), 404
    
    return jsonify({
        'id': question.id,
        'content': question.content,
        'type': question.type,
        'difficulty': question.difficulty,
        'subject': question.subject,
        'options': question.options,
        'answer': question.answer,
        'explanation': question.explanation
    })