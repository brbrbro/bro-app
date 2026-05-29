from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

from routes import auth as _auth_routes