"""Run native Terraform with an argument vector (also avoids PowerShell argument splitting)."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
root = pathlib.Path(__file__).resolve().parents[1]
part = sys.argv[1]
assert part in ('bootstrap', 'main')
terraform = shutil.which('terraform') or str(root / '.tools' / 'terraform' / 'terraform.exe')
gcloud = shutil.which('gcloud')
env = os.environ.copy()
env.update(CLOUDSDK_CORE_DISABLE_FILE_LOGGING='1', CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK='1', CLOUDSDK_CORE_DISABLE_PROMPTS='1')
if not env.get('GOOGLE_OAUTH_ACCESS_TOKEN') and not env.get('GOOGLE_APPLICATION_CREDENTIALS'):
    env['GOOGLE_OAUTH_ACCESS_TOKEN'] = subprocess.check_output([gcloud, 'auth', 'print-access-token'], env=env, text=True).strip()
env['TF_VAR_project_id'] = 'triodelicia-mensal4-2026'
if part == 'bootstrap':
    repo = json.loads(subprocess.check_output(['gh', 'api', 'repos/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp'], text=True))
    env['TF_VAR_repository_id'] = str(repo['id'])
    env['TF_VAR_repository_owner_id'] = str(repo['owner']['id'])
    billing = json.loads(subprocess.check_output([gcloud, 'billing', 'projects', 'describe', 'triodelicia-mensal4-2026', '--billing-project=triodelicia-mensal4-2026', '--format=json'], env=env, text=True))
    if not billing.get('billingEnabled'): raise RuntimeError('Billing authorization has not completed')
    env['TF_VAR_billing_account_id'] = billing['billingAccountName'].split('/')[-1]
directory = root / 'infra' / 'terraform' / part
private = root / '.local'; private.mkdir(exist_ok=True)
plan = private / (part + '.tfplan')
result = subprocess.run([terraform, '-chdir=' + str(directory), 'plan', '-input=false', '-no-color', '-out=' + str(plan)], env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
(private / (part + '-plan.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
if result.returncode:
    print(result.stderr[-5000:]); sys.exit(result.returncode)
data = json.loads(subprocess.check_output([terraform, '-chdir=' + str(directory), 'show', '-json', str(plan)], env=env, text=True, encoding='utf-8'))
evidence = root / 'docs' / 'evidencias'; evidence.mkdir(parents=True, exist_ok=True)
destination = evidence / ('terraform-' + part + '-plan.json')
public = json.dumps(data, indent=2)
if part == 'bootstrap':
    public = public.replace(env['TF_VAR_billing_account_id'], '[REDACTED_BILLING_ACCOUNT]')
destination.write_text(public, encoding='utf-8')
print(json.dumps({'plan': part, 'changes': [{'address': x['address'], 'actions': x['change']['actions']} for x in data.get('resource_changes', [])]}, indent=2))
if part == 'main': subprocess.run([sys.executable, str(root / 'scripts' / 'check-plan.py'), str(destination)], check=True)
