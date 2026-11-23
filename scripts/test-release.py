"""Real image rollback test; same application source, different image configs.

Tests operational recovery rather than application schema migrations.
"""
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.error
from smoke import call
ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.local' / 'release-test'
WORK.mkdir(parents=True, exist_ok=True)
source_project = os.environ.get('COMPOSE_PROJECT_NAME', 'todo-implementation')
project = 'todo-release-test'
bash = shutil.which('bash') if os.name != 'nt' else r'C:\Program Files\Git\bin\bash.exe'
def run(command, env=None, allow_failure=False):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode and not allow_failure:
        raise RuntimeError(result.stdout[-1500:] + result.stderr[-2500:])
    return result
def compose(*args): return run(['docker', 'compose', '-p', source_project, *args])
def wait(version):
    for _ in range(45):
        try:
            if call('http://127.0.0.1:8080', '/health/ready')[1]['version'] == version: return
        except urllib.error.URLError: pass
        time.sleep(2)
    raise RuntimeError('Expected release did not become ready: ' + version)
secret_dir = WORK / 'secrets'; secret_dir.mkdir(exist_ok=True)
if (secret_dir / 'mongodb_uri').exists(): (secret_dir / 'mongodb_uri').chmod(0o600)
shutil.copyfile(ROOT / '.local' / 'secrets' / 'mongodb_uri', secret_dir / 'mongodb_uri')
(secret_dir / 'mongodb_uri').chmod(0o444)
template = (ROOT / 'infra' / 'ansible' / 'roles' / 'application' / 'templates' / 'compose.yml.j2').read_text()
template += f'    networks: [default, database]\nnetworks:\n  database:\n    external: true\n    name: {source_project}_database\n'
(WORK / 'compose.yml').write_text(template)
if (WORK / 'release.env').exists():
    run(['docker', 'compose', '-p', project, '--env-file', str(WORK / 'release.env'), '-f', str(WORK / 'compose.yml'), 'down'])
for release_file in ('release.env', 'release.previous.env', 'release.failed.env'):
    (WORK / release_file).unlink(missing_ok=True)
(WORK / '.dockerignore').write_text('*\n!backend-version.Dockerfile\n')
(WORK / 'backend-version.Dockerfile').write_text('FROM todo-backend:local\nARG VERSION\nENV APP_VERSION=$VERSION\nLABEL org.opencontainers.image.revision=$VERSION\n')
for version in ('release-a', 'release-b'):
    run(['docker', 'build', '--load', '-f', str(WORK / 'backend-version.Dockerfile'), '-t', 'todo-backend:' + version, '--build-arg', 'VERSION=' + version, str(WORK)])
(WORK / 'backend-version.Dockerfile').write_text('FROM todo-backend:local\nCMD ["node", "-e", "process.exit(1)"]\n')
run(['docker', 'build', '--load', '-f', str(WORK / 'backend-version.Dockerfile'), '-t', 'todo-backend:broken', str(WORK)])
env = dict(os.environ, TODO_ROOT=str(WORK).replace('\\', '/'), COMPOSE_FILE=str(WORK / 'compose.yml').replace('\\', '/'), COMPOSE_PROJECT_NAME=project, MSYS_NO_PATHCONV='1', TODO_DEPLOY_WAIT_SECONDS='30')
def deploy(*args, allow_failure=False): return run([bash, 'scripts/deploy-images.sh', *args], env=env, allow_failure=allow_failure)
def image(): return run(['docker', 'inspect', project + '-backend-1', '--format', '{{.Image}}']).stdout.strip()
compose('stop', 'frontend', 'backend')
try:
    deploy('todo-frontend:local', 'todo-backend:release-a', 'release-a'); wait('release-a'); image_a = image()
    deploy('todo-frontend:local', 'todo-backend:release-b', 'release-b'); wait('release-b'); image_b = image()
    assert image_a != image_b
    deploy('rollback'); wait('release-a'); assert image() == image_a, f'Rollback image {image()} != first release {image_a}'
    failure = deploy('todo-frontend:local', 'todo-backend:broken', 'broken', allow_failure=True)
    assert failure.returncode != 0
    wait('release-a'); assert image() == image_a
    evidence = {'passed': True, 'cloud_test': False, 'healthy_image_a': image_a, 'healthy_image_b': image_b, 'checks': ['different image IDs deployed', 'manual rollback restored image A', 'failed deployment returned nonzero and restored healthy image A'], 'limit': 'Same application source, distinct image configs; no schema migration tested.'}
    (ROOT / 'docs' / 'evidencias' / 'local-rollback.json').write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence))
finally:
    run(['docker', 'compose', '-p', project, '--env-file', str(WORK / 'release.env'), '-f', str(WORK / 'compose.yml'), 'stop'], allow_failure=True)
    compose('up', '-d', '--wait', '--wait-timeout', '120')
