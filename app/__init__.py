import os
from flask import Flask, jsonify

from .database import db
from .services.errors import AppError
from app.services.org_service import OrgService
from app.services.event_service import EventService
from app.services.announcement_service import AnnouncementService


def create_app():
    app = Flask(__name__)

    # -----------------------------
    # BASE DIRECTORY
    # -----------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

    # -----------------------------
    # DATABASE PATH (data/database)
    # -----------------------------
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'database')
    os.makedirs(DATA_DIR, exist_ok=True)

    DB_PATH = os.path.join(DATA_DIR, 'campus_org_hub.db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    db.init_app(app)

    # -----------------------------
    # APPLICATION CONTEXT
    # -----------------------------
    with app.app_context():
        from . import models
        db.create_all()

        # Import initial data
        OrgService.import_from_csv()
        EventService.import_from_csv()
        AnnouncementService.import_from_csv()

    # -----------------------------
    # REGISTER BLUEPRINTS
    # -----------------------------
    from .routes.auth_routes import auth_bp
    from .routes.org_routes import org_bp
    from .routes.application_routes import app_bp
    from .routes.event_routes import event_bp
    from .routes.web_routes import web_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(org_bp, url_prefix='/api/orgs')
    app.register_blueprint(app_bp, url_prefix='/api/applications')
    app.register_blueprint(event_bp, url_prefix='/api/events')
    app.register_blueprint(web_bp)

    # -----------------------------
    # ERROR HANDLERS
    # -----------------------------
    @app.errorhandler(AppError)
    def handle_app_error(err):
        response = jsonify({
            "error": err.message,
            "code": err.code
        })
        response.status_code = err.http_status
        return response

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal Server Error"}), 500

    return app
