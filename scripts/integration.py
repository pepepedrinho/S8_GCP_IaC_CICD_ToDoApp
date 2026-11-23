"""Integration against real Docker/Mongo: persistence, readiness and isolated recovery."""
import json
import os
import pathlib
import subprocess
import time
import urllib.error
from smoke import call
ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = os.environ.get('TODO_TEST_URL', 'http://127.0.0.1:8080')
PROJECT = os.environ.get('COMPOSE_PROJECT_NAME', 'todo-implementation')
def compose(*args, env=None):
    subprocess.run(['docker', 'compose', '-p', PROJECT, *args], cwd=ROOT, env=env, check=True, capture_output=True)
def wait():
    for _ in range(60):
        try:
            if call(BASE, '/health/ready')[0] == 200: return
        except (urllib.error.URLError, ConnectionError): pass
        time.sleep(2)
    raise RuntimeError('API did not recover')
wait()
_, todo = call(BASE, '/todos', 'POST', {'text': 'Persistencia ' + str(time.time_ns())})
path = '/todos/' + todo['_id']
assert call(BASE, path, 'PATCH')[1]['completed'] is True
checks = []
def preserved(label):
    wait()
    restored = next(x for x in call(BASE, '/todos')[1] if x['_id'] == todo['_id'])
    assert restored['text'] == todo['text'] and restored['completed'] is True
    checks.append(label)
try:
    compose('restart', 'mongo', 'backend'); preserved('restart preserves document and state')
    compose('up', '-d', '--no-deps', '--force-recreate', 'mongo'); preserved('database recreation preserves named volume')
    env = dict(os.environ, APP_VERSION='integration-update')
    compose('up', '-d', '--no-deps', 'backend', env=env); preserved('application update preserves data')
    assert call(BASE, '/health/live')[1]['version'] == 'integration-update'
    compose('up', '-d', '--no-deps', 'backend'); preserved('application configuration rollback preserves data')
    compose('stop', 'mongo')
    try: call(BASE, '/health/ready'); raise AssertionError('Readiness must fail without DB')
    except urllib.error.HTTPError as error: assert error.code == 503
    assert call(BASE, '/health/live')[0] == 200
    checks.append('database outage yields readiness 503 and liveness 200')
    compose('start', 'mongo'); preserved('database recovery')
finally:
    compose('start', 'mongo')
    wait()
    call(BASE, path, 'DELETE')
result = {'passed': True, 'database': 'real MongoDB', 'checks': checks, 'cloud_test': False}
target = ROOT / 'docs' / 'evidencias' / 'local-integration.json'
target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
