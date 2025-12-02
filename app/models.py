from .database import db
from datetime import datetime
from passlib.hash import pbkdf2_sha256 as hasher

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

class User(BaseModel):
    __tablename__ = 'users'
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), default='student')  # student, officer, admin
    full_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = hasher.hash(password)

    def verify_password(self, password):
        return hasher.verify(password, self.password_hash)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat()
        }

class Organization(BaseModel):
    __tablename__ = 'organizations'
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    officers = db.Column(db.String(512), nullable=True)  # CSV of usernames / IDs for simplicity
    contact_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        officers_list = []
        if self.officers:
            officers_list = [o.strip() for o in self.officers.split(',') if o.strip()]
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'officers': officers_list,
            'contact_email': self.contact_email,
            'created_at': self.created_at.isoformat()
        }

class Application(BaseModel):
    __tablename__ = 'applications'
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    statement = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='pending')  # pending, accepted, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    applicant = db.relationship('User', backref='applications')
    organization = db.relationship('Organization', backref='applications')

    def to_dict(self):
        return {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'org_id': self.org_id,
            'statement': self.statement,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat()
        }

class Event(BaseModel):
    __tablename__ = 'events'
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref='events')

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat()
        }

class Message(BaseModel):
    __tablename__ = 'messages'
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    receiver_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver_user = db.relationship('User', foreign_keys=[receiver_user_id])
    receiver_org = db.relationship('Organization')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_org_id': self.receiver_org_id,
            'receiver_user_id': self.receiver_user_id,
            'content': self.content,
            'sent_at': self.sent_at.isoformat()
        }
