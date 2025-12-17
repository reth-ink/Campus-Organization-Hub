import sqlite3
import os
from flask import g, current_app

def get_db():
    if 'db' not in g:
        db_path = None
        try:
            # prefer Flask app config if available
            db_path = current_app.config.get('DATABASE')
        except Exception:
            db_path = None
        if not db_path:
            db_path = os.environ.get('DATABASE') or 'campus_hub.db'
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        try:
            # Ensure SQLite enforces foreign key constraints (ON DELETE CASCADE)
            g.db.execute('PRAGMA foreign_keys = ON')
        except Exception:
            # Not critical; continue without failing app startup
            pass
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        # Prefer using the provided SQL schema (database/schema_v1.sql) so the
        # table/column names match the CSV files and model classes.
        try:
            schema_path = os.path.abspath(os.path.join(app.root_path, '..', 'database', 'schema_v1.sql'))
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    sql = f.read()
                # Make CREATE TABLE statements idempotent
                sql = sql.replace('\nCREATE TABLE ', '\nCREATE TABLE IF NOT EXISTS ')
                db.executescript(sql)
            else:
                # Fallback: create a minimal set of tables if the schema file is missing
                cursor = db.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                    FirstName TEXT,
                    LastName TEXT,
                    Email TEXT UNIQUE
                )
                ''')
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS organizations (
                    OrgID INTEGER PRIMARY KEY AUTOINCREMENT,
                    OrgName TEXT,
                    OrgDescription TEXT
                )
                ''')
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS memberships (
                    MembershipID INTEGER PRIMARY KEY AUTOINCREMENT,
                    UserID INTEGER,
                    OrgID INTEGER,
                    Status TEXT
                )
                ''')
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS officer_roles (
                    OfficerRoleID INTEGER PRIMARY KEY AUTOINCREMENT,
                    MembershipID INTEGER,
                    RoleName TEXT,
                    RoleStart DATETIME,
                    RoleEnd DATETIME
                )
                ''')
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    EventID INTEGER PRIMARY KEY AUTOINCREMENT,
                    OrgID INTEGER,
                    CreatedBy INTEGER,
                    EventName TEXT,
                    EventDescription TEXT,
                    EventDate TEXT,
                    Location TEXT
                )
                ''')
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    AnnouncementID INTEGER PRIMARY KEY AUTOINCREMENT,
                    OrgID INTEGER,
                    CreatedBy INTEGER,
                    Title TEXT,
                    Content TEXT,
                    DatePosted TEXT
                )
                ''')
                db.commit()
        except Exception as e:
            # If schema application fails, continue — app startup shouldn't be blocked
            # but log the problem so the developer can diagnose schema issues
            try:
                app.logger.exception('Failed to apply SQL schema during init_db')
            except Exception:
                # app.logger may not be available in some contexts; fall back to printing
                import traceback; traceback.print_exc()
        # Attempt to seed data from CSV files in the repository's data/ folder
        # Import service modules here to avoid circular imports at module import time
        # Allow skipping automatic seeding by setting SKIP_AUTO_SEED in the environment
        if os.environ.get('SKIP_AUTO_SEED') is None:
            try:
                data_dir = os.path.abspath(os.path.join(app.root_path, '..', 'data'))

                # Lazy imports to avoid circular import issues
                from .services.organization_service import OrgService
                from .services.user_service import UserService
                from .services.event_service import EventService
                from .services.announcement_service import AnnouncementService
                from .services.membership_service import MembershipService
                from .services.officer_role_service import OfficerRoleService

                def table_count(table_name):
                    try:
                        row = db.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()
                        return int(row['cnt']) if row is not None else 0
                    except Exception as e:
                        try:
                            app.logger.debug('table_count error for %s: %s', table_name, e)
                        except Exception:
                            pass
                        return 0

                # Only import when the table is empty and the CSV file exists
                if table_count('organizations') == 0:
                    org_csv = os.path.join(data_dir, 'organizations.csv')
                    if os.path.exists(org_csv):
                        try:
                            OrgService.import_organizations_from_csv(org_csv)
                        except Exception as e:
                            app.logger.exception('Failed to import organizations from CSV')

                if table_count('users') == 0:
                    users_csv = os.path.join(data_dir, 'users.csv')
                    if os.path.exists(users_csv):
                        try:
                            UserService.import_users_from_csv(users_csv)
                        except Exception as e:
                            app.logger.exception('Failed to import users from CSV')

                if table_count('events') == 0:
                    events_csv = os.path.join(data_dir, 'events.csv')
                    if os.path.exists(events_csv):
                        try:
                            EventService.import_events_from_csv(events_csv)
                        except Exception as e:
                            app.logger.exception('Failed to import events from CSV')

                if table_count('announcements') == 0:
                    ann_csv = os.path.join(data_dir, 'announcements.csv')
                    if os.path.exists(ann_csv):
                        try:
                            AnnouncementService.import_announcements_from_csv(ann_csv)
                        except Exception as e:
                            app.logger.exception('Failed to import announcements from CSV')

                if table_count('memberships') == 0:
                    mem_csv = os.path.join(data_dir, 'membership.csv')
                    if os.path.exists(mem_csv):
                        try:
                            MembershipService.import_memberships_from_csv(mem_csv)
                        except Exception as e:
                            app.logger.exception('Failed to import memberships from CSV')

                if table_count('officer_roles') == 0:
                    officers_csv = os.path.join(data_dir, 'officer_roles.csv')
                    if os.path.exists(officers_csv):
                        try:
                            OfficerRoleService.import_officer_roles_from_csv(officers_csv)
                        except Exception as e:
                            app.logger.exception('Failed to import officer_roles from CSV')
            except Exception as e:
                try:
                    app.logger.exception('Automatic seeding failed during init_db')
                except Exception:
                    import traceback; traceback.print_exc()

        app.teardown_appcontext(close_db)

