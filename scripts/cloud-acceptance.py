"""Real acceptance tests on the two already provisioned academic VMs.

Only the task created by this test is removed. Database volumes are preserved.
"""
import json
import argparse
import pathlib
import re
import socket
import time
import urllib.error
from cloud import ROOT, snapshot, ssh
from smoke import call

parser = argparse.ArgumentParser()
parser.add_argument('--comparison-commit', default='')
args = parser.parse_args()
assert not args.comparison_commit or re.fullmatch(r'[a-f0-9]{40}', args.comparison_commit)

state = snapshot()
assert all(state[n]['status'] == 'RUNNING' for n in ('todo-app', 'todo-db'))
base = state['url']
checks = []
measurements = {}
target = ROOT / 'docs/evidencias/gcp-acceptance.json'

def wait():
    for _ in range(90):
        try:
            if call(base, '/health/ready')[0] == 200: return
        except (urllib.error.URLError, ConnectionError): pass
        time.sleep(2)
    raise RuntimeError('Public HTTPS readiness did not recover')

def preserved():
    wait()
    item = next(t for t in call(base, '/todos')[1] if t['_id'] == task['_id'])
    assert item['text'] == task['text'] and item['completed'] is True

wait()
for port in (22, 27017, 3128):
    try:
        connection = socket.create_connection((state['todo-app']['public_ip'], port), timeout=4)
    except OSError:
        checks.append(f'public TCP {port} unavailable')
    else:
        connection.close()
        raise AssertionError(f'Administrative/database port {port} is public')
ssh('todo-app', "python3 -c \"import socket; s=socket.create_connection(('10.42.0.20',27017),timeout=5); s.close()\"")
checks.append('application reaches Mongo on private address; database has no public IP')
_, task = call(base, '/todos', 'POST', {'text': 'GCP persistence acceptance ' + str(time.time_ns())})
task_path = '/todos/' + task['_id']
assert call(base, task_path, 'PATCH')[1]['completed'] is True
ssh('todo-db', 'sudo systemctl stop todo-backup.timer')
try:
    ssh('todo-db', 'sudo docker compose -f /opt/todo/compose.yml restart mongo')
    preserved(); checks.append('Mongo restart preserves task and completed state')
    ssh('todo-db', 'sudo docker compose -f /opt/todo/compose.yml up -d --no-deps --force-recreate --pull never --wait --wait-timeout 180 mongo')
    preserved(); checks.append('Mongo container recreation preserves dedicated persistent disk')
    original = ssh('todo-app', 'sudo cat /opt/todo/release.env')
    release = dict(line.split('=', 1) for line in original.splitlines() if '=' in line)
    for value in release.values(): assert re.fullmatch(r'[a-zA-Z0-9./:@_-]+', value)
    if args.comparison_commit and args.comparison_commit != release['APP_VERSION']:
        def image_id():
            return ssh('todo-app', "sudo docker inspect $(sudo docker compose --env-file /opt/todo/release.env -f /opt/todo/compose.yml ps -q backend) --format '{{.Image}}'")
        previous_image = image_id()
        prefix = 'ghcr.io/pepepedrinho/s8_gcp_iac_cicd_todoapp'
        ssh('todo-app', f'sudo docker image inspect {prefix}-backend:{args.comparison_commit} >/dev/null || sudo docker load -i /opt/todo/artifacts/application.tar')
        ssh('todo-app', f'sudo /opt/todo/bin/deploy-images.sh {prefix}-frontend:{args.comparison_commit} {prefix}-backend:{args.comparison_commit} {args.comparison_commit}')
        preserved(); assert image_id() != previous_image
        assert call(base, '/health/live')[1]['version'] == args.comparison_commit
        ssh('todo-app', 'sudo /opt/todo/bin/deploy-images.sh rollback')
        preserved(); assert image_id() == previous_image
        checks.append('distinct GHCR image deployed and original image restored by rollback; task preserved')
    # Identified configuration update exercises the production deploy script;
    # distinct image replacement is performed separately by the deploy workflow.
    version = release['APP_VERSION'] + '-acceptance'
    ssh('todo-app', f"sudo /opt/todo/bin/deploy-images.sh {release['FRONTEND_IMAGE']} {release['BACKEND_IMAGE']} {version}")
    preserved(); assert call(base, '/health/live')[1]['version'] == version
    checks.append('versioned application configuration update preserves data')
    ssh('todo-app', 'sudo /opt/todo/bin/deploy-images.sh rollback')
    preserved(); assert call(base, '/health/live')[1]['version'] == release['APP_VERSION']
    checks.append('production rollback restores previous version and preserves task')
    ssh('todo-db', 'sudo docker compose -f /opt/todo/compose.yml stop mongo')
    try:
        call(base, '/health/ready')
        raise AssertionError('Readiness did not fail without Mongo')
    except urllib.error.HTTPError as error: assert error.code == 503
    assert call(base, '/health/live')[0] == 200
    checks.append('database outage yields readiness503 and liveness200 over HTTPS')
    ssh('todo-db', 'sudo docker compose -f /opt/todo/compose.yml up -d --pull never --wait --wait-timeout 180')
    preserved()
    ssh('todo-db', 'sudo systemctl start todo-backup.service')
    preserved()
    manifest = json.loads(ssh('todo-db', "sudo python3 -c \"import pathlib,json; p=max(pathlib.Path('/opt/todo/backups').glob('todo-*.archive.gz.json')); print(p.read_text())\""))
    assert manifest['validated'] is True
    checks.append('systemd backup service completed with isolated restore, hash check and private GCS uploads')
    # Download the uploaded copy with the database runtime identity and repeat
    # checksum + isolated recovery, without granting backups access to CI.
    object_name = 'todo/todo-' + manifest['created_utc'] + '.archive.gz'
    ssh('todo-db', f"sudo /opt/todo/bin/gcs.py download triodelicia-mensal4-2026-todo-backups {object_name} /opt/todo/backups/downloaded.archive.gz")
    ssh('todo-db', f"sudo /opt/todo/bin/gcs.py download triodelicia-mensal4-2026-todo-backups {object_name}.json /opt/todo/backups/downloaded.archive.gz.json")
    ssh('todo-db', 'sudo /opt/todo/bin/verify-backup.py /opt/todo/backups/downloaded.archive.gz')
    preserved(); checks.append('GCS copy downloaded and restored in isolated volume without overwriting production')
    for name in ('todo-app', 'todo-db'):
        measurements[name] = ssh(name, "free -b; sudo docker stats --no-stream --format '{{json .}}'; sudo docker inspect $(sudo docker ps -aq) --format '{{.Name}} OOMKilled={{.State.OOMKilled}}'")
    result = {'passed': True, 'cloud_test': True, 'url': base, 'checks': checks, 'backup_manifest': manifest, 'runtime_measurements': measurements, 'state': state}
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
finally:
    ssh('todo-db', 'sudo docker compose -f /opt/todo/compose.yml up -d --pull never --wait --wait-timeout 180')
    ssh('todo-db', 'sudo systemctl start todo-backup.timer')
    wait()
    call(base, task_path, 'DELETE')
