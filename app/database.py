from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app, csv_file=None):
    db.init_app(app)
    with app.app_context():
        db.create_all()

        if csv_file:
            from .models import User, Organization
            import csv

            # Load CSV into database if empty
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Example CSV columns: UserID, FirstName, LastName, Email
                    if not User.query.filter_by(Email=row['Email']).first():
                        user = User(
                            FirstName=row['FirstName'],
                            LastName=row['LastName'],
                            Email=row['Email']
                        )
                        user.set_password(row.get('Password', 'password123'))
                        db.session.add(user)
            db.session.commit()
