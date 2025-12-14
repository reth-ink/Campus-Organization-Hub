from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    UserID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(80), nullable=False)
    LastName = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships = db.relationship('Membership', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)

    def to_dict(self):
        return {
            "UserID": self.UserID,
            "FirstName": self.FirstName,
            "LastName": self.LastName,
            "Email": self.Email,
        }

    def __repr__(self):
        return f"<User {self.FirstName} {self.LastName}>"


class Organization(db.Model):
    __tablename__ = 'organizations'
    OrgID = db.Column(db.Integer, primary_key=True)
    OrgName = db.Column(db.String(120), nullable=False, unique=True)
    Description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships = db.relationship('Membership', back_populates='organization', cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', back_populates='organization', cascade='all, delete-orphan')
    events = db.relationship('Event', back_populates='organization', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.OrgID,
            "name": self.OrgName,
            "description": self.Description,
            "officers": [o.RoleName for m in self.memberships for o in m.officer_roles],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Organization {self.OrgName}>"


class Membership(db.Model):
    __tablename__ = 'memberships'
    MembershipID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    OrgID = db.Column(db.Integer, db.ForeignKey('organizations.OrgID'), nullable=False)
    Status = db.Column(db.String(20), default='Pending')
    DateApplied = db.Column(db.DateTime, default=datetime.utcnow)
    DateApproved = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='memberships')
    organization = db.relationship('Organization', back_populates='memberships')
    officer_roles = db.relationship('OfficerRole', back_populates='membership', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "MembershipID": self.MembershipID,
            "UserID": self.UserID,
            "OrgID": self.OrgID,
            "Status": self.Status,
            "DateApplied": self.DateApplied.isoformat() if self.DateApplied else None,
            "DateApproved": self.DateApproved.isoformat() if self.DateApproved else None,
        }

    def __repr__(self):
        return f"<Membership UserID={self.UserID} OrgID={self.OrgID}>"


class OfficerRole(db.Model):
    __tablename__ = 'officer_roles'
    OfficerRoleID = db.Column(db.Integer, primary_key=True)
    MembershipID = db.Column(db.Integer, db.ForeignKey('memberships.MembershipID'), nullable=False)
    RoleName = db.Column(db.String(50), nullable=False)
    StartDate = db.Column(db.DateTime, default=datetime.utcnow)
    EndDate = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    membership = db.relationship('Membership', back_populates='officer_roles')
    announcements = db.relationship('Announcement', back_populates='creator', cascade='all, delete-orphan')
    events = db.relationship('Event', back_populates='creator', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "OfficerRoleID": self.OfficerRoleID,
            "MembershipID": self.MembershipID,
            "RoleName": self.RoleName,
            "StartDate": self.StartDate.isoformat() if self.StartDate else None,
            "EndDate": self.EndDate.isoformat() if self.EndDate else None,
        }

    def __repr__(self):
        return f"<OfficerRole {self.RoleName} MembershipID={self.MembershipID}>"


class Announcement(db.Model):
    __tablename__ = 'announcements'
    AnnouncementID = db.Column(db.Integer, primary_key=True)
    OrgID = db.Column(db.Integer, db.ForeignKey('organizations.OrgID'), nullable=False)
    CreatedBy = db.Column(db.Integer, db.ForeignKey('officer_roles.OfficerRoleID'), nullable=False)
    Title = db.Column(db.String(200), nullable=False)
    Content = db.Column(db.Text, nullable=False)
    DatePosted = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='announcements')
    creator = db.relationship('OfficerRole', back_populates='announcements')

    def to_dict(self):
        return {
            "AnnouncementID": self.AnnouncementID,
            "OrgID": self.OrgID,
            "CreatedBy": self.CreatedBy,
            "Title": self.Title,
            "Content": self.Content,
            "DatePosted": self.DatePosted.isoformat() if self.DatePosted else None,
        }

    def __repr__(self):
        return f"<Announcement {self.Title} OrgID={self.OrgID}>"


class Event(db.Model):
    __tablename__ = 'events'
    EventID = db.Column(db.Integer, primary_key=True)
    OrgID = db.Column(db.Integer, db.ForeignKey('organizations.OrgID'), nullable=False)
    CreatedBy = db.Column(db.Integer, db.ForeignKey('officer_roles.OfficerRoleID'), nullable=False)
    EventName = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.Text)
    EventDate = db.Column(db.DateTime)
    Location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='events')
    creator = db.relationship('OfficerRole', back_populates='events')

    def to_dict(self):
        return {
            "EventID": self.EventID,
            "OrgID": self.OrgID,
            "CreatedBy": self.CreatedBy,
            "EventName": self.EventName,
            "Description": self.Description,
            "EventDate": self.EventDate.isoformat() if self.EventDate else None,
            "Location": self.Location,
        }

    def __repr__(self):
        return f"<Event {self.EventName} OrgID={self.OrgID}>"
