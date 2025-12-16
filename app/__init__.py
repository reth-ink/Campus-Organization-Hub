from flask import Flask, jsonify, render_template

from app.routes import officer_role_routes
from .database import init_db
from .utils.errors import AppError
from .routes import user_routes, organization_routes, event_routes, announcement_routes, membership_routes, officer_role_routes, web_routes

def create_app():
    app = Flask(__name__)
    app.config['DATABASE'] = 'campus_hub.db'
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

    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({'code': e.code, 'error': e.message}), 400

    @app.errorhandler(Exception)
    def handle_general_error(e):
        return jsonify({'code': 'GENERAL_ERROR', 'error': str(e)}), 500

    return app

"""
Object-Oriented Programming (OOP) — Use of classes, inheritance, encapsulation,
and abstraction for organizing code into modules and services.
2. Data Handling — Reading, writing, transforming, and querying structured data (CSV,
JSON, or database).
3. Lambda Functions — Use of lambda expressions for quick transformations, sorting,
filtering, and callbacks.
4. Error Handling — Robust use of try/except/finally, custom exceptions, and
graceful failure handling in all modules.
5. File Handling — Stream-based I/O using context managers for importing/exporting data
(CSV/JSON/Text).
6. Flask Web Framework — Building a web-based application using Flask, applying
routing, templates, and blueprints.
7. Database Integration — Using SQLite (built-in) or another RDBMS with sqlite3 or
an ORM like SQLAlchemy for persistent data storage.
B. General Requirements
• Developed in Python 3.10+ using Flask for the web interface.
• Must include OOP structure, with separate modules for models, services, routes, and
database access.
• At least 5 functional modules/features.
• Must demonstrate use of lambda functions in data processing.
• Must include robust error handling across the application.
• Must perform file import/export using CSV or JSON.
• Must integrate a database for data persistence (e.g., SQLite).
• Must use Flask for the main interface.
• Must include at least 20 records per table.

project should have all of the following features:
"""