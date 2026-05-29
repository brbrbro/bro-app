from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    openid_hash = db.Column(db.String(64), unique=True, nullable=False)
    nickname = db.Column(db.String(100))
    avatar = db.Column(db.String(500))
    region = db.Column(db.String(20), default='mainland')
    member_type = db.Column(db.String(20), default='free')
    gold = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20))
    syllabus = db.Column(db.String(100))
    knowledge_point = db.Column(db.String(200))
    type = db.Column(db.String(20), nullable=False)
    difficulty = db.Column(db.Integer, default=3)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    options = db.Column(db.Text)
    solved_count = db.Column(db.Integer, default=0)
    correct_rate = db.Column(db.Float, default=0)
    source = db.Column(db.String(20), default='seed')
    status = db.Column(db.String(20), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    status = db.Column(db.String(20), default='done')
    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    time_spent = db.Column(db.Integer, default=0)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

class Share(db.Model):
    __tablename__ = 'shares'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ImportBatch(db.Model):
    __tablename__ = 'import_batches'
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(20), nullable=False)
    source_file = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    total_questions = db.Column(db.Integer, default=0)
    parsed_questions = db.Column(db.Integer, default=0)
    approved_questions = db.Column(db.Integer, default=0)
    exam_type = db.Column(db.String(20))
    subject = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    knowledge_point = db.Column(db.String(200))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class ParsedQuestion(db.Model):
    __tablename__ = 'parsed_questions'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('import_batches.id'))
    raw_content = db.Column(db.Text)
    content = db.Column(db.Text)
    options = db.Column(db.Text)
    answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    images = db.Column(db.Text)
    formulas = db.Column(db.Text)
    exam_type = db.Column(db.String(20))
    subject = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    knowledge_point = db.Column(db.String(200))
    type = db.Column(db.String(20))
    difficulty = db.Column(db.Integer, default=3)
    status = db.Column(db.String(20), default='pending')
    confidence = db.Column(db.Float)
    review_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuestionImage(db.Model):
    __tablename__ = 'question_images'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer)
    image_type = db.Column(db.String(20))
    original_url = db.Column(db.String(500))
    processed_url = db.Column(db.String(500))
    ocr_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
