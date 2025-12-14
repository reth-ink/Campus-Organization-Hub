import csv
from datetime import datetime
import os
from app import create_app
from app.database import db
from app.models import User, Organization, Membership, OfficerRole, Announcement, Event

app = create_app()

CSV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sample_data.csv')

with app.app_context():
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # User
            user = User(
                UserID=int(row['UserID']),
                FirstName=row['FirstName'],
                LastName=row['LastName'],
                Email=row['Email']
            )
            db.session.merge(user)

            # Organization
            org = Organization(
                OrgID=int(row['OrgID']),
                OrgName=row['OrgName'],
                Description=row['OrgDescription']
            )
            db.session.merge(org)

            # Membership
            membership = Membership(
                MembershipID=int(row['MembershipID']),
                UserID=int(row['UserID']),
                OrgID=int(row['OrgID']),
                Status=row['Status'],
                DateApplied=datetime.fromisoformat(row['DateApplied']),
                DateApproved=datetime.fromisoformat(row['DateApproved']) if row['DateApproved'] else None
            )
            db.session.merge(membership)

            # OfficerRole
            officer = OfficerRole(
                OfficerRoleID=int(row['OfficerRoleID']),
                MembershipID=int(row['MembershipID']),
                RoleName=row['RoleName'],
                StartDate=datetime.fromisoformat(row['RoleStart']),
                EndDate=datetime.fromisoformat(row['RoleEnd']) if row['RoleEnd'] else None
            )
            db.session.merge(officer)

            # Announcement
            announcement = Announcement(
                AnnouncementID=int(row['AnnouncementID']),
                OrgID=int(row['OrgID']),
                CreatedBy=int(row['OfficerRoleID']),
                Title=row['AnnouncementTitle'],
                Content=row['AnnouncementContent'],
                DatePosted=datetime.fromisoformat(row['AnnouncementDate'])
            )
            db.session.merge(announcement)

            # Event
            event = Event(
                EventID=int(row['EventID']),
                OrgID=int(row['OrgID']),
                CreatedBy=int(row['OfficerRoleID']),
                EventName=row['EventName'],
                Description=row['EventDescription'],
                EventDate=datetime.fromisoformat(row['EventDate']),
                Location=row['Location']
            )
            db.session.merge(event)

    db.session.commit()
    print("Database seeded successfully!")
