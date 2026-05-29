from flask import Blueprint
import importlib

questions_bp = Blueprint('questions', __name__)
users_bp = Blueprint('users', __name__)
shares_bp = Blueprint('shares', __name__)
progress_bp = Blueprint('progress', __name__)
sync_bp = Blueprint('sync', __name__)
import_bp = Blueprint('import', __name__)

def register_blueprints(app):
    from . import questions, shares, sync, users, progress
    # import.py is a reserved keyword, use importlib
    importlib.import_module('.import', 'routes')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
