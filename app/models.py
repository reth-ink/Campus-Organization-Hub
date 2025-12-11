from .database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    UserID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(80), nullable=False)
    LastName = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)

class Organization(db.Model):
    __tablename__ = 'organizations'
    OrgID = db.Column(db.Integer, primary_key=True)
    OrgName = db.Column(db.String(120), nullable=False)
    Description = db.Column(db.Text)

class Membership(db.Model):
    __tablename__ = 'memberships'
    MembershipID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    OrgID = db.Column(db.Integer, db.ForeignKey('organizations.OrgID'), nullable=False)
    Status = db.Column(db.String(20), default='Pending')
    DateApplied = db.Column(db.DateTime, default=datetime.utcnow)
    DateApproved = db.Column(db.DateTime)

class OfficerRole(db.Model):
    __tablename__ = 'officer_roles'
    OfficerRoleID = db.Column(db.Integer, primary_key=True)
    MembershipID = db.Column(db.Integer, db.ForeignKey('memberships.MembershipID'), nullable=False)
    RoleName = db.Column(db.String(50), nullable=False)
    StartDate = db.Column(db.DateTime, default=datetime.utcnow)
    EndDate = db.Column(db.DateTime)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    AnnouncementID = db.Column(db.Integer, primary_key=True)
    OrgID = db.Column(db.Integer, db.ForeignKey('organizations.OrgID'), nullable=False)
    CreatedBy = db.Column(db.Integer, db.ForeignKey('officer_roles.OfficerRoleID'), nullable=False)
    Title = db.Column(db.String(200), nullable=False)
    Content = db.Column(db.Text, nullable=False)
    DatePosted = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    __tablename__ = 'events'
    EventID = db.Column(db.Integer, primary_key=True)
    OrgID = db.Column(db.Integer, db.ForeignKey('organizations.OrgID'), nullable=False)
    CreatedBy = db.Column(db.Integer, db.ForeignKey('officer_roles.OfficerRoleID'), nullable=False)
    EventName = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.Text)
    EventDate = db.Column(db.DateTime)
    Location = db.Column(db.String(200))
