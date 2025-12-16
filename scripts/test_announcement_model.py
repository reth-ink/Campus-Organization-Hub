import importlib.util
import os

# Load the announcement model module directly (avoids importing the app package)
here = os.path.dirname(__file__)
model_path = os.path.abspath(os.path.join(here, '..', 'app', 'models', 'announcement.py'))
spec = importlib.util.spec_from_file_location('ann_model', model_path)
ann_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ann_mod)

Announcement = ann_mod.Announcement

row = {'AnnouncementID': 1, 'OrgID': 2, 'CreatedBy': 3, 'Title': 'Hi', 'Content': 'Hello', 'DatePosted': '2025-12-16', 'created_at': '2025-12-16 12:00:00'}
a = Announcement(**row)
print('OK', a.AnnouncementID, a.created_at)
