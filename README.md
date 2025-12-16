# Campus Organization Hub
Campus Organization Hub is a comprehensive platform designed to streamline the management and engagement of campus organizations. It provides tools for organization administration, event management, and announcements.

## Members
- Reth Jerrod Rodriguez
- John Michael Alfarita
- Lowell Sutarez Jr.
- Brent Justine Balingit
- Jim John Ebreo

## Setup & Run (development)

Follow these steps to get the app running locally on Windows (PowerShell examples). The project expects Python 3.10+.

1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. (Optional) Set a secret for Flask sessions

```powershell
# $env:FLASK_SECRET = 'replace-with-a-secret'
```

4. Seed the database (recommended)

This project ships with a CLI seeder at `scripts/seed_db.py` that imports CSV files from the `data/` folder and applies the SQL schema in `database/schema_v1.sql`.

- To recreate the database and import all CSVs (recommended for a fresh start):

```powershell
# $env:SEED_DEFAULT_PASSWORD = 'pass123'  # optional: sets default password for seeded users
python .\scripts\seed_db.py --recreate-db
```

- If you want to prevent automatic seeding when the Flask app initializes (the app does a best-effort auto-seed unless disabled), set:

```powershell
# $env:SKIP_AUTO_SEED = '1'
```

The seeder uses the CSV files in the `data/` folder and the canonical SQL in `database/schema_v1.sql`. If you prefer not to recreate the DB, run the seeder without `--recreate-db` to attempt a safe import.

5. Run the app

```powershell
python run.py
```

Open http://127.0.0.1:5000/ in your browser.

6. Quick checks / test scripts

There are a couple of small helper scripts under `scripts/` used by the project for quick verification (they import model files directly to avoid requiring Flask to be installed):

- `scripts/test_org_model.py` — verifies `Organization` model accepts DB-style dicts.
- `scripts/test_models.py` — simple instantiation checks for `Event` and `OfficerRole` models.

Run them like:

```powershell
python .\scripts\test_models.py
```

Troubleshooting
- If you see `ModuleNotFoundError: No module named 'flask'` when running the app or scripts that import the app, make sure your venv is activated and `pip install -r requirements.txt` completed successfully.
- If seeded users cannot log in, ensure `SEED_DEFAULT_PASSWORD` was set before seeding (or that the seeded CSVs contained passwords). The seeder defaults to a safe placeholder if none is provided.
- If you run into foreign key constraint errors when creating announcements/events via the web UI, note the schema: `CreatedBy` in `announcements` and `events` references `officer_roles.OfficerRoleID`. The web UI currently stores `session['user_id']` as the logged-in user id; if you need `CreatedBy` to reference an officer role, we should add a mapping from user->officer role (I can implement this).

Notes
- Automatic seeding: the app attempts a best-effort seed on startup using `database/schema_v1.sql` and CSVs in `data/` unless `SKIP_AUTO_SEED` is set.
- Password hashing: the project uses `passlib` with `pbkdf2_sha256` for seeded and created users (no native bcrypt dependency required).

If you'd like, I can add a short `CONTRIBUTING.md` or a one-click PowerShell script that wraps venv creation, install, seeding, and run steps.