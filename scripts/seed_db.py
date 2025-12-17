#!/usr/bin/env python3
"""
scripts/seed_db.py

Run CSV imports (explicitly) and print errors and table counts.
Run from repository root:
    python scripts/seed_db.py
Re-run and recreate DB:
    python scripts/seed_db.py --recreate-db
"""
import os
import sys
import argparse

# Ensure the repository root is on sys.path so imports like `from app import ...`
# work when this script is run as `python scripts/seed_db.py` (the script's
# directory becomes the first entry in sys.path, which doesn't include the repo root).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app import create_app
from app.database import get_db


def run_import(service, func_name, csv_path, errors):
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path} — skipping")
        
        return
    try:
        getattr(service, func_name)(csv_path)
        print(f"Imported {os.path.basename(csv_path)}")
    except Exception as e:
        errors.append((os.path.basename(csv_path), str(e)))
        print(f"Error importing {os.path.basename(csv_path)}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Seed the campus_hub database from CSV files.')
    parser.add_argument('--recreate-db', action='store_true', help='Delete existing campus_hub.db before creating schema')
    args = parser.parse_args()

    # Optionally remove existing DB so schema_v1.sql can be applied fresh
    repo_db = os.path.abspath(os.path.join(REPO_ROOT, 'campus_hub.db'))
    if args.recreate_db:
        if os.path.exists(repo_db):
            print(f"Removing existing DB at {repo_db}")
            os.remove(repo_db)

        # Determine and print the default password that will be used for seeded users
        # (can be overridden with SEED_DEFAULT_PASSWORD environment variable).
        default_pw = os.environ.get('SEED_DEFAULT_PASSWORD', 'pass123')
        print(f"Using default seed password: {default_pw} (override with SEED_DEFAULT_PASSWORD)")

    # Prevent the app's automatic seeding (init_db) from running — this script
    # will perform imports explicitly to avoid double-imports and UNIQUE errors.
    os.environ['SKIP_AUTO_SEED'] = '1'
    app = create_app()
    with app.app_context():
        data_dir = os.path.abspath(os.path.join(app.root_path, '..', 'data'))

        # Lazy import services to avoid circular imports
        from app.services.organization_service import OrgService
        from app.services.user_service import UserService
        from app.services.event_service import EventService
        from app.services.announcement_service import AnnouncementService
        from app.services.membership_service import MembershipService
        from app.services.officer_role_service import OfficerRoleService

        errors = []

        # Import order matters because of FOREIGN KEY constraints:
        # - memberships reference users and organizations
        # - officer_roles reference memberships
        # - events and announcements reference officer_roles and organizations
        # Therefore import in this order: organizations, users, memberships, officer_roles, events, announcements
        run_import(OrgService, 'import_organizations_from_csv', os.path.join(data_dir, 'organizations.csv'), errors)
        run_import(UserService, 'import_users_from_csv', os.path.join(data_dir, 'users.csv'), errors)
        run_import(MembershipService, 'import_memberships_from_csv', os.path.join(data_dir, 'membership.csv'), errors)
        run_import(OfficerRoleService, 'import_officer_roles_from_csv', os.path.join(data_dir, 'officer_roles.csv'), errors)
        run_import(EventService, 'import_events_from_csv', os.path.join(data_dir, 'events.csv'), errors)
        run_import(AnnouncementService, 'import_announcements_from_csv', os.path.join(data_dir, 'announcements.csv'), errors)

        db = get_db()
        tables = ['organizations', 'users', 'events', 'announcements', 'memberships', 'officer_roles']

        print('\nRow counts:')
        for t in tables:
            try:
                r = db.execute(f"SELECT COUNT(*) as cnt FROM {t}").fetchone()
                cnt = r['cnt'] if r and 'cnt' in r.keys() else (r[0] if r else 0)
                print(f"{t}: {cnt}")
            except Exception as e:
                print(f"{t}: error ({e})")

    if errors:
        print('\nSome imports failed:')
        for csv, err in errors:
            print(f"{csv}: {err}")
        sys.exit(1)
    else:
        print('\nSeeding completed successfully.')


if __name__ == '__main__':
    main()
