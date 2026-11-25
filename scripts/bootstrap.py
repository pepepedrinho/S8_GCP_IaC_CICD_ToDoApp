"""Owner-only initial bootstrap; requires pre-approved billing and a saved reviewed plan."""
import json
import argparse
import os
import pathlib
import shutil
import subprocess
root = pathlib.Path(__file__).resolve().parents[1]
private = root / '.local'
parser = argparse.ArgumentParser()
parser.add_argument('--migrate-only', action='store_true', help='Resume backend migration after a successful apply')
args = parser.parse_args()
tf = shutil.which('terraform') or str(root / '.tools' / 'terraform' / 'terraform.exe')
gcloud = shutil.which('gcloud')
env = os.environ.copy()
env.update(CLOUDSDK_CORE_DISABLE_FILE_LOGGING='1', CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK='1', CLOUDSDK_CORE_DISABLE_PROMPTS='1')
env['GOOGLE_OAUTH_ACCESS_TOKEN'] = subprocess.check_output([gcloud, 'auth', 'print-access-token'], text=True, env=env).strip()
directory = root / 'infra' / 'terraform' / 'bootstrap'
plan = private / 'bootstrap.tfplan'
if not args.migrate_only:
    assert plan.exists(), 'Run and review terraform-plan.py bootstrap first'
    run = subprocess.run([tf, '-chdir=' + str(directory), 'apply', '-input=false', '-no-color', str(plan)], env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (private / 'bootstrap-apply.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    if run.returncode:
        print((run.stdout + run.stderr)[-5500:]); raise SystemExit(run.returncode)
    outputs = json.loads(subprocess.check_output([tf, '-chdir=' + str(directory), 'output', '-json'], env=env, text=True, encoding='utf-8'))
    (private / 'bootstrap-outputs.json').write_text(json.dumps(outputs, indent=2), encoding='utf-8')
else:
    outputs = json.loads((private / 'bootstrap-outputs.json').read_text(encoding='utf-8'))
assert outputs['state_bucket']['value'] == 'triodelicia-mensal4-2026-todo-state'
# The bucket must exist before backend migration: break the bootstrap cycle.
(directory / 'backend.generated.tf').write_text('terraform {\n  backend "gcs" {}\n}\n', encoding='utf-8')
subprocess.run([tf, '-chdir=' + str(directory), 'init', '-input=false', '-migrate-state', '-force-copy', '-backend-config=bucket=' + outputs['state_bucket']['value'], '-backend-config=prefix=todo/bootstrap'], env=env, check=True)
subprocess.run([tf, '-chdir=' + str(root / 'infra' / 'terraform' / 'main'), 'init', '-input=false', '-reconfigure', '-backend-config=bucket=' + outputs['state_bucket']['value'], '-backend-config=prefix=todo/main'], env=env, check=True)
print(json.dumps({'bootstrap': 'applied', 'remote_state': 'migrated', 'vms_created': 0, 'outputs': {k: v['value'] for k, v in outputs.items()}}, indent=2))
