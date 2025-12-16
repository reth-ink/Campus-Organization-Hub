import os
import importlib.util

# Load the organization model module directly (avoids importing the app package)
here = os.path.dirname(__file__)
model_path = os.path.abspath(os.path.join(here, '..', 'app', 'models', 'organization.py'))
spec = importlib.util.spec_from_file_location('org_model', model_path)
org_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(org_mod)

Organization = org_mod.Organization

row = {'OrgID': 1, 'OrgName': 'Test Org', 'Description': 'desc from DB'}
o = Organization(**row)
print('OK', o.OrgDescription)
