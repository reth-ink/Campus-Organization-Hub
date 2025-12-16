from flask import Flask, jsonify, render_template, session

from app.routes import officer_role_routes
from .database import init_db
from .utils.errors import AppError
from .routes import user_routes, organization_routes, event_routes, announcement_routes, membership_routes, officer_role_routes, web_routes

def create_app(config: dict = None):
    app = Flask(__name__)
    # default database path
    app.config['DATABASE'] = 'campus_hub.db'
    # apply optional overrides (used by tests)
    if config:
        app.config.update(config)
    # Secret key used for sessions (can be overridden by environment)
    import os
    app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

    init_db(app)

    app.register_blueprint(user_routes.bp)
    app.register_blueprint(organization_routes.bp)
    app.register_blueprint(event_routes.bp)
    app.register_blueprint(announcement_routes.bp)
    app.register_blueprint(membership_routes.bp)
    app.register_blueprint(officer_role_routes.bp)
    app.register_blueprint(web_routes.bp)

    # Inject current_user into templates
    @app.context_processor
    def inject_current_user():
        user_id = session.get('user_id')
        if not user_id:
            return {'current_user': None}
        try:
            from .services.user_service import UserService
            user = UserService.get_user_row_by_id(user_id)
            return {'current_user': user}
        except Exception:
            return {'current_user': None}

    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({'code': e.code, 'error': e.message}), 400

    @app.errorhandler(Exception)
    def handle_general_error(e):
        return jsonify({'code': 'GENERAL_ERROR', 'error': str(e)}), 500

    return app

