from flask import Blueprint
import importlib

questions_bp = Blueprint('questions', __name__)
users_bp = Blueprint('users', __name__)
shares_bp = Blueprint('shares', __name__)
progress_bp = Blueprint('progress', __name__)
sync_bp = Blueprint('sync', __name__)
import_bp = Blueprint('import', __name__)
leaderboard_bp = Blueprint('leaderboard', __name__)
checkin_bp = Blueprint('checkin', __name__)
exchange_bp = Blueprint('exchange', __name__)
invite_bp = Blueprint('invite', __name__)
lexicon_bp = Blueprint('lexicon', __name__)
notification_bp = Blueprint('notification', __name__)

def register_blueprints(app):
    from . import questions, shares, sync, users, progress, leaderboard, checkin, exchange, invite, lexicon, notification
    importlib.import_module('.import', 'routes')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
    app.register_blueprint(checkin_bp, url_prefix='/api/checkin')
    app.register_blueprint(exchange_bp, url_prefix='/api/exchange')
    app.register_blueprint(invite_bp, url_prefix='/api/invite')
    app.register_blueprint(lexicon_bp, url_prefix='/api/lexicon')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
