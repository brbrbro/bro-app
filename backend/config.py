import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bro-dev-secret-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///C:/bro-dev/bro.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'bro-jwt-secret-change-later'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # AI 配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = 'gpt-4-vision-preview'
    OCR_LANGUAGE = 'chi_sim+eng'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = '/var/www/bro/uploads'