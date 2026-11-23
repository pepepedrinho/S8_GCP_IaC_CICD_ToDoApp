"""Configure this fork without printing secrets or replacing an unknown credential."""
import json
import pathlib
import secrets
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = 'pepepedrinho/S8_GCP_IaC_CICD_ToDoApp'

def gh(*args, value=None):
    result = subprocess.run(['gh', *args, '-R', REPO], input=value, capture_output=True, text=True, encoding='utf-8')
    if result.returncode: raise RuntimeError(result.stderr)
    return result.stdout

existing = {item['name'] for item in json.loads(gh('secret', 'list', '--json', 'name'))}
private = ROOT / '.local' / 'cloud-secrets.json'
if not private.exists():
    if existing & {'MONGO_ROOT_PASSWORD', 'MONGO_APP_PASSWORD'}:
        raise RuntimeError('Remote Mongo secrets already exist; preserve them and recover the matching local secure copy before proceeding.')
    private.parent.mkdir(exist_ok=True)
    private.write_text(json.dumps({name: secrets.token_hex(24) for name in ('mongo_root_password', 'mongo_app_password')}), encoding='utf-8')
    private.chmod(0o600)
values = json.loads(private.read_text(encoding='utf-8'))
if set(values) != {'mongo_root_password', 'mongo_app_password'}:
    raise ValueError('Both Mongo credentials are required')
for name, value in values.items():
    if name not in ('mongo_root_password', 'mongo_app_password') or len(value) < 24:
        raise ValueError('Invalid credential configuration')
    if name.upper() not in existing:
        gh('secret', 'set', name.upper(), value=value)
variables = {
    'GCP_WIF_PROVIDER': 'projects/271680307280/locations/global/workloadIdentityPools/todo-github/providers/github',
    'GCP_SERVICE_ACCOUNT': 'todo-automation@triodelicia-mensal4-2026.iam.gserviceaccount.com',
}
current = {item['name']: item['value'] for item in json.loads(gh('variable', 'list', '--json', 'name,value'))}
for name, value in variables.items():
    if name in current and current[name] != value:
        raise RuntimeError('Conflicting GitHub variable: ' + name)
    if name not in current: gh('variable', 'set', name, value=value)
result = {
    'repository': REPO,
    'secrets_present': sorted(item['name'] for item in json.loads(gh('secret', 'list', '--json', 'name'))),
    'variables_present': sorted(item['name'] for item in json.loads(gh('variable', 'list', '--json', 'name'))),
    'secret_values_logged': False,
    'gcp_identity_checked': False,
    'note': 'Only GitHub settings configured; verify GCP identities through the separately approved bootstrap.'
}
(ROOT / 'docs' / 'evidencias' / 'github-configuration.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
