import re
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODELS_DIR = os.path.join(ROOT, 'app', 'models')
TEMPLATES_DIR = os.path.join(ROOT, 'app', 'templates')

# get model to_dict keys by regex
model_keys = {}
for fname in os.listdir(MODELS_DIR):
    if not fname.endswith('.py'):
        continue
    path = os.path.join(MODELS_DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    # find the to_dict return block
    m = re.search(r'return\s*\{([^}]+)\}', src, re.DOTALL)
    keys = set()
    if m:
        body = m.group(1)
        for k in re.findall(r"['\"]([A-Za-z0-9_]+)['\"]\s*:\s*", body):
            keys.add(k)
    model_keys[fname] = keys

# scan templates for {{ var.key }} patterns
template_keys = {}
pattern = re.compile(r"{{\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)")
for root, dirs, files in os.walk(TEMPLATES_DIR):
    for fname in files:
        if not fname.endswith('.html'):
            continue
        path = os.path.join(root, fname)
        with open(path, 'r', encoding='utf-8') as f:
            txt = f.read()
        for var, key in pattern.findall(txt):
            template_keys.setdefault(fname, set()).add((var, key))

# heuristics: map common variable names to model files
var_to_model = {
    'org': 'organization.py',
    'orgs': 'organization.py',
    'event': 'event.py',
    'events': 'event.py',
    'announcement': 'announcement.py',
    'announcements': 'announcement.py',
    'user': 'user.py',
    'users': 'user.py',
    'membership': 'membership.py',
    'memberships': 'membership.py',
    'officer': 'officer_role.py',
    'officer_role': 'officer_role.py',
    'officers': 'officer_role.py'
}

mismatches = []
for tpl, items in template_keys.items():
    for var, key in items:
        model_file = var_to_model.get(var)
        if not model_file:
            # unknown variable; skip
            continue
        keys = model_keys.get(model_file, set())
        if key not in keys:
            mismatches.append((tpl, var, key, model_file))

if not mismatches:
    print('No mismatches detected between templates and model to_dict keys.')
else:
    print('Detected mismatches:')
    for tpl, var, key, model_file in mismatches:
        print(f"Template {tpl} references {var}.{key} but {model_file} to_dict keys are {sorted(list(model_keys.get(model_file, [])))}")

print('\nSummary of models and their keys:')
for m, ks in model_keys.items():
    print(m + ':', sorted(list(ks)))

print('\nScanned templates:')
for t, items in template_keys.items():
    print(t + ':', sorted(list(items)))
