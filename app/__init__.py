import os
from flask import Flask, jsonify
from .database import db
from .routes.auth_routes import auth_bp
from .routes.org_routes import org_bp
from .routes.application_routes import app_bp
from .routes.event_routes import event_bp
from .routes.file_routes import file_bp
from .services.errors import AppError
from .routes.web_routes import web_bp


def create_app(config_object=None):
    app = Flask(__name__)
    # Basic config - can be overridden by environment variables or a config object
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///campus_hub.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    db.init_app(app)

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(org_bp, url_prefix='/api/orgs')
    app.register_blueprint(app_bp, url_prefix='/api/applications')
    app.register_blueprint(event_bp, url_prefix='/api/events')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    app.register_blueprint(web_bp)
    
    # global error handlers
    @app.errorhandler(AppError)
    def handle_app_error(err):
        response = jsonify({'error': err.message, 'code': err.code})
        response.status_code = err.http_status
        return response

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal Server Error'}), 500

    return app
