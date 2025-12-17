import csv
import sqlite3
from flask import current_app
from ..database import get_db
from ..models.officer_role import OfficerRole
from ..utils.errors import AppError

class OfficerRoleService:

    @staticmethod
    def create_officer_role(name, permissions):
        db = get_db()
        try:
            # create a role template not tied to a membership
            db.execute(
                'INSERT INTO officer_roles (MembershipID, RoleName, StartDate, EndDate, can_post_announcements, can_create_events, can_approve_members, can_assign_roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (None, name, None, None, int(bool(permissions.get('can_post_announcements'))), int(bool(permissions.get('can_create_events'))), int(bool(permissions.get('can_approve_members'))), int(bool(permissions.get('can_assign_roles'))))
            )
            db.commit()
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while creating officer role')
            raise AppError('DB_ERROR', 'Could not create officer role', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while creating officer role')
            raise AppError('DB_ERROR', 'Could not create officer role', original_exception=e)

    @staticmethod
    def get_all_officer_roles():
        db = get_db()
        # select canonical columns from schema (StartDate/EndDate) — model accepts these
        try:
            rows = db.execute(
                'SELECT OfficerRoleID, MembershipID, RoleName, StartDate, EndDate, can_post_announcements, can_create_events, can_approve_members, can_assign_roles FROM officer_roles'
            ).fetchall()
        except sqlite3.DatabaseError as e:
            current_app.logger.debug('Permission columns missing or DB error when querying officer_roles: %s', e)
            # older DB schema: permission columns may not exist yet
            rows = db.execute('SELECT OfficerRoleID, MembershipID, RoleName, StartDate, EndDate FROM officer_roles').fetchall()
        except Exception as e:
            current_app.logger.exception('Unexpected error retrieving officer roles')
            rows = db.execute('SELECT OfficerRoleID, MembershipID, RoleName, StartDate, EndDate FROM officer_roles').fetchall()

        return [OfficerRole(**dict(row)).to_dict() for row in rows]

    @staticmethod
    def import_officer_roles_from_csv(file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for r in reader:
                    # CSV uses OfficerRoleID, MembershipID, RoleName, RoleStart, RoleEnd
                    membership = r.get('MembershipID') or r.get('membership_id')
                    role_name = r.get('RoleName') or r.get('name')
                    role_start = r.get('StartDate') or r.get('RoleStart')
                    role_end = r.get('EndDate') or r.get('RoleEnd')
                    try:
                        db = get_db()
                        db.execute('INSERT OR IGNORE INTO officer_roles (OfficerRoleID, MembershipID, RoleName, StartDate, EndDate, can_post_announcements, can_create_events, can_approve_members, can_assign_roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                   (r.get('OfficerRoleID'), membership, role_name, role_start, role_end, r.get('can_post_announcements') or 0, r.get('can_create_events') or 0, r.get('can_approve_members') or 0, r.get('can_assign_roles') or 0))
                        db.commit()
                    except sqlite3.DatabaseError as e:
                        current_app.logger.exception('Database error while creating officer role from CSV')
                        raise AppError('DB_ERROR', 'Could not create officer role from CSV', original_exception=e)
                    except Exception as e:
                        current_app.logger.exception('Unexpected error while creating officer role from CSV')
                        raise AppError('DB_ERROR', 'Could not create officer role from CSV', original_exception=e)
        except (csv.Error, OSError) as e:
            current_app.logger.exception('Error reading officer_roles CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error importing officer_roles from CSV')
            raise AppError('CSV_IMPORT_ERROR', 'Error importing CSV', original_exception=e)

    @staticmethod
    def get_or_create_officer_role_for_user(org_id, user_id, role_name='Creator'):
        """
        Given an organization id and a user id, return an OfficerRoleID suitable
        to use as CreatedBy in announcements/events. The implementation tries
        to find a Membership for the (user, org) pair, then an OfficerRole for
        that Membership. If missing, it will create the Membership (status
        'member') and/or the OfficerRole (RoleName defaults to role_name).

        Returns: OfficerRoleID (int)
        """
        try:
            db = get_db()
            # Find existing membership
            mem_row = db.execute('SELECT MembershipID FROM memberships WHERE UserID = ? AND OrgID = ? LIMIT 1', (user_id, org_id)).fetchone()
            if mem_row and mem_row['MembershipID']:
                membership_id = mem_row['MembershipID']
            else:
                # create membership and use its id. Use 'Approved' for the creator so the org
                # immediately appears in their Joined Organizations list. If you prefer
                # creator memberships to be subject to approval, change this to 'Pending'.
                cur = db.execute('INSERT INTO memberships (UserID, OrgID, Status, DateApplied, DateApproved) VALUES (?, ?, ?, ?, ?)',
                                 (user_id, org_id, 'Approved', None, None))
                db.commit()
                membership_id = cur.lastrowid

            # Try to find an officer role for that membership
            orow = db.execute('SELECT OfficerRoleID FROM officer_roles WHERE MembershipID = ? LIMIT 1', (membership_id,)).fetchone()
            if orow and orow['OfficerRoleID']:
                return orow['OfficerRoleID']

            # create an officer role linked to this membership
            # Default to an admin-like role for creators: grant all useful permissions
            cur2 = db.execute('INSERT INTO officer_roles (MembershipID, RoleName, StartDate, EndDate, can_post_announcements, can_create_events, can_approve_members, can_assign_roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                              (membership_id, role_name, None, None, 1, 1, 1, 1))
            db.commit()
            return cur2.lastrowid
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error in get_or_create_officer_role_for_user')
            raise AppError('DB_ERROR', 'Could not map user to officer role', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error in get_or_create_officer_role_for_user')
            raise AppError('DB_ERROR', 'Could not map user to officer role', original_exception=e)

    @staticmethod
    def assign_role_to_membership(membership_id, role_name, permissions=None):
        """Assign a role to a membership with explicit permissions."""
        db = get_db()
        try:
            perms = permissions or {}
            cur = db.execute('INSERT INTO officer_roles (MembershipID, RoleName, StartDate, EndDate, can_post_announcements, can_create_events, can_approve_members, can_assign_roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                             (membership_id, role_name, None, None, int(bool(perms.get('can_post_announcements'))), int(bool(perms.get('can_create_events'))), int(bool(perms.get('can_approve_members'))), int(bool(perms.get('can_assign_roles')))))
            db.commit()
            return cur.lastrowid
        except sqlite3.DatabaseError as e:
            current_app.logger.exception('Database error while assigning role to membership')
            raise AppError('DB_ERROR', 'Could not assign role to membership', original_exception=e)
        except Exception as e:
            current_app.logger.exception('Unexpected error while assigning role to membership')
            raise AppError('DB_ERROR', 'Could not assign role to membership', original_exception=e)

    @staticmethod
    def user_permissions_for_org(org_id, user_id):
        """Return aggregated permission flags for a user within an organization."""
        db = get_db()
        try:
            mem = db.execute('SELECT MembershipID, Status FROM memberships WHERE USERID = ? AND OrgID = ? LIMIT 1', (user_id, org_id)).fetchone()
        except sqlite3.DatabaseError as e:
            current_app.logger.debug('DB error while fetching membership in user_permissions_for_org: %s', e)
            return {'can_post_announcements': 0, 'can_create_events': 0, 'can_approve_members': 0, 'can_assign_roles': 0}
        except Exception as e:
            current_app.logger.exception('Unexpected error while fetching membership in user_permissions_for_org')
            return {'can_post_announcements': 0, 'can_create_events': 0, 'can_approve_members': 0, 'can_assign_roles': 0}
        # sqlite3.Row does not implement .get(), convert to dict for safe access
        if mem:
            mem = dict(mem)

        if not mem or not mem.get('MembershipID'):
            return {'can_post_announcements': 0, 'can_create_events': 0, 'can_approve_members': 0, 'can_assign_roles': 0}

        membership_id = mem['MembershipID']
        try:
            # include RoleName so we can detect explicit 'Admin' roles
            rows = db.execute('SELECT RoleName, can_post_announcements, can_create_events, can_approve_members, can_assign_roles FROM officer_roles WHERE MembershipID = ?', (membership_id,)).fetchall()
        except sqlite3.DatabaseError as e:
            current_app.logger.debug('DB error while fetching officer roles in user_permissions_for_org: %s', e)
            return {'can_post_announcements': 0, 'can_create_events': 0, 'can_approve_members': 0, 'can_assign_roles': 0}
        except Exception as e:
            current_app.logger.exception('Unexpected error while fetching officer roles in user_permissions_for_org')
            return {'can_post_announcements': 0, 'can_create_events': 0, 'can_approve_members': 0, 'can_assign_roles': 0}

        # aggregate permissions (if any role grants a permission, user has it)
        perms = {'can_post_announcements': 0, 'can_create_events': 0, 'can_approve_members': 0, 'can_assign_roles': 0}
        for r in rows:
            # rows may be sqlite3.Row objects; convert to dict for safe .get use
            rr = dict(r)
            # If the role is explicitly 'Admin', grant all permissions
            role_name = (rr.get('RoleName') or '')
            if isinstance(role_name, str) and role_name.lower() == 'admin':
                return {'can_post_announcements': 1, 'can_create_events': 1, 'can_approve_members': 1, 'can_assign_roles': 1}
            perms['can_post_announcements'] = perms['can_post_announcements'] or int(rr.get('can_post_announcements') or 0)
            perms['can_create_events'] = perms['can_create_events'] or int(rr.get('can_create_events') or 0)
            perms['can_approve_members'] = perms['can_approve_members'] or int(rr.get('can_approve_members') or 0)
            perms['can_assign_roles'] = perms['can_assign_roles'] or int(rr.get('can_assign_roles') or 0)

        return perms

    @staticmethod
    def get_officers_by_org(org_id):
        """Return a list of officers (with user_name, user_id, role_name and permissions) for a given org."""
        db = get_db()
        try:
            # join officer_roles -> memberships -> users to get user info and permissions
            # Exclude plain 'Member' roles from the officers list — only show users who hold an officer-type role
            rows = db.execute(
                '''SELECT orf.OfficerRoleID, orf.MembershipID, orf.RoleName, orf.can_post_announcements, orf.can_create_events, orf.can_approve_members, orf.can_assign_roles,
                    m.UserID as UserID, m.OrgID as OrgID, u.FirstName as FirstName, u.LastName as LastName
                   FROM officer_roles orf
                   JOIN memberships m ON m.MembershipID = orf.MembershipID
                   JOIN users u ON u.UserID = m.UserID
                   WHERE m.OrgID = ? AND LOWER(orf.RoleName) != 'member' ''', (org_id,)
            ).fetchall()
        except sqlite3.DatabaseError as e:
            # fallback: if permission columns missing or join fails, attempt a simpler join
            current_app.logger.debug('DB error in complex officer join, attempting simpler join: %s', e)
            try:
                # fallback simpler join: still exclude rows with RoleName 'Member'
                rows = db.execute(
                    "SELECT orf.OfficerRoleID, orf.MembershipID, orf.RoleName, m.UserID as UserID, m.OrgID as OrgID, u.FirstName as FirstName, u.LastName as LastName FROM officer_roles orf JOIN memberships m ON m.MembershipID = orf.MembershipID JOIN users u ON u.UserID = m.UserID WHERE m.OrgID = ? AND LOWER(orf.RoleName) != 'member'",
                    (org_id,)
                ).fetchall()
            except Exception as e:
                current_app.logger.exception('Simpler officer join failed')
                return []
        except Exception as e:
            current_app.logger.exception('Unexpected error retrieving officers by org')
            return []

        officers = []
        for r in rows:
            # convert sqlite3.Row to dict for consistent access
            rd = dict(r)
            try:
                user_name = f"{rd.get('FirstName')} {rd.get('LastName')}"
            except Exception as e:
                current_app.logger.debug('Failed to build user_name for officer row: %s', e)
                user_name = 'Unknown'
            role_name_val = (rd.get('RoleName') or rd.get('role_name') or '')
            is_admin_role = isinstance(role_name_val, str) and role_name_val.lower() == 'admin'
            officers.append({
                'OfficerRoleID': rd.get('OfficerRoleID'),
                'MembershipID': rd.get('MembershipID'),
                'RoleName': role_name_val,
                'role_name': role_name_val,
                'user_name': user_name,
                'UserID': rd.get('UserID'),
                'can_post_announcements': 1 if is_admin_role else int(rd.get('can_post_announcements') or 0),
                'can_create_events': 1 if is_admin_role else int(rd.get('can_create_events') or 0),
                'can_approve_members': 1 if is_admin_role else int(rd.get('can_approve_members') or 0),
                'can_assign_roles': 1 if is_admin_role else int(rd.get('can_assign_roles') or 0),
            })

        return officers

    @staticmethod
    def get_user_by_officer_role(officer_role_id):
        """Resolve an OfficerRoleID to the underlying user row (dict) if possible.
        Returns a dict with UserID, FirstName, LastName or None.
        """
        db = get_db()
        try:
            row = db.execute(
                'SELECT u.UserID as UserID, u.FirstName as FirstName, u.LastName as LastName FROM officer_roles orf JOIN memberships m ON m.MembershipID = orf.MembershipID JOIN users u ON u.UserID = m.UserID WHERE orf.OfficerRoleID = ? LIMIT 1',
                (officer_role_id,)
            ).fetchone()
            return dict(row) if row is not None else None
        except Exception as e:
            current_app.logger.debug('Error resolving user by officer role: %s', e)
            return None