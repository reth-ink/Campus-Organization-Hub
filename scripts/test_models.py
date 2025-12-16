# Simple test that loads model files directly and instantiates them with schema-style keys
import importlib.util
import os

root = os.path.dirname(__file__)

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

# Event
event_path = os.path.abspath(os.path.join(root, '..', 'app', 'models', 'event.py'))
event_mod = load_module(event_path, 'event_model')
E = event_mod.Event
row = {'EventID': 1, 'OrgID': 2, 'CreatedBy': 3, 'EventName': 'Party', 'Description': 'Fun time', 'EventDate': '2025-12-20', 'Location': 'Hall'}
e = E(**row)
print('Event OK:', e.EventDescription)

# OfficerRole
or_path = os.path.abspath(os.path.join(root, '..', 'app', 'models', 'officer_role.py'))
or_mod = load_module(or_path, 'officer_model')
OR = or_mod.OfficerRole
r = {'OfficerRoleID': 10, 'MembershipID': 5, 'RoleName': 'President', 'StartDate': '2024-01-01', 'EndDate': '2024-12-31'}
o = OR(**r)
print('OfficerRole OK:', o.RoleStart, o.RoleEnd)
