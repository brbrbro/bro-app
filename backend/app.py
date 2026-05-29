from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes import register_blueprints

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
CORS(app)
db.init_app(app)
jwt = JWTManager(app)
register_blueprints(app)

with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "service": "bro-backend",
        "status": "ok",
        "version": "1.0.0",
        "db": "connected"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)