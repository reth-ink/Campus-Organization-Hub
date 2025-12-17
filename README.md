# Campus Organization Hub
Campus Organization Hub is a comprehensive platform designed to streamline the management and engagement of campus organizations. It provides tools for organization administration, event management, and announcements.

## Members
- Reth Jerrod Rodriguez
- John Michael Alfarita
- Lowell Sutarez Jr.
- Brent Justine Balingit
- Jim John Ebreo

## Developer guide — quick navigation & debugging

This project is a small Flask app backed by SQLite. The following notes are intended to help contributors quickly find code, debug common issues, and run the app locally.

Key files & folders
- `run.py` — app entrypoint used in development to start the Flask server.
- `app/__init__.py` and `app/routes/__init__.py` — app factory and route registration.
- `app/routes/web_routes.py` — most page routes, form handlers, and permission checks; first place to look for routing/permission bugs.
- `app/services/` — business logic and DB access helpers (e.g., `AnnouncementService`, `OrgService`). Keep I/O here; pure logic belongs to models or service helpers.
- `app/models/` — lightweight model classes (DTOs) for `User`, `Organization`, `Announcement`, etc.
- `app/templates/` — Jinja2 templates. `base.html` contains the main layout and the toast container for flash messages.
- `app/static/styles.css` — global styling. `app/static/admin.css` is a page-scoped override for admin pages.
- `database/schema_v1.sql` — canonical DB schema. Useful for inspecting FK constraints and table layout.
- `scripts/seed_db.py` — CSV-based seeding script (run during local setup). Order matters: organizations -> users -> memberships -> officer_roles -> events -> announcements.

Common debugging tips
- Foreign key / seed errors: If `scripts/seed_db.py` fails with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`, check the CSV import order and that referenced IDs exist (announcements reference `officer_roles.OfficerRoleID`).
- Wrong template behavior / layout issues: Layout problems are usually CSS-related. Check `app/static/styles.css` and look for `.home-layout` / `.feed` rules. Admin pages use `app/static/admin.css` to avoid inheriting the home grid rules.
- Flash/notification issues: Flashes are rendered in `base.html` inside the `#toast-container`; CSS `.toast` controls visibility and positioning. JS in `base.html` auto-hides toasts.
- Permission-related flow (can't create event/announcement): Permissions are set on `officer_roles` (flags: `can_post_announcements`, `can_create_events`) and resolved via `OfficerRoleService.user_permissions_for_org(...)`.
- File uploads: uploaded attachments are saved under `app/static/uploads` — check permissions and available disk space if uploads fail.

Useful local commands
- Create / activate a virtualenv (Windows PowerShell):
	```powershell
	python -m venv .venv; .\.venv\Scripts\Activate.ps1
	pip install -r requirements.txt
	```
- Initialize or reseed the DB (use the repository's seed script):
	```powershell
	python scripts/seed_db.py --recreate
	```
- Run the app (development):
	```powershell
	python run.py
	```

Quick pointers for common edits
- Add page-scoped CSS: put the file under `app/static/` (e.g. `admin.css`) and include it in the template by using the `extra_head` block in `base.html`.
- Fix button/link targets in templates: search `app/templates/` for `url_for('web.` to locate route usages. Update routes in `app/routes/web_routes.py` if behavior should change.
- Where permissions are enforced: look for `OfficerRoleService.user_permissions_for_org(...)` in `app/routes/web_routes.py` and services.

If you'd like, I can also:
- Add a one-page quick-reference cheat sheet (fields & model attributes) to this README.
- Add a `DEVELOPMENT.md` file with step-by-step local setup and a short troubleshooting checklist.


