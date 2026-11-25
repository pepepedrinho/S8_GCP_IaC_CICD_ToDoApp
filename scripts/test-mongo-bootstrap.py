"""Test interrupted-init recovery against an isolated real Mongo, without wiping data."""
import json
import pathlib
import secrets
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
name = 'todo-bootstrap-recovery-' + secrets.token_hex(6)
def run(*args, allow_failure=False):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    if result.returncode and not allow_failure: raise RuntimeError(result.stderr[-1200:])
    return result
def mongo(*args, allow_failure=False):
    return run('exec', name, 'mongosh', '--quiet', *args, allow_failure=allow_failure)

run('volume', 'create', name)
mounts = []
for source, destination in [
    (ROOT/'.local/secrets/mongo_root_password', '/run/secrets/mongo_root_password'),
    (ROOT/'.local/secrets/mongo_app_password', '/run/secrets/mongo_app_password'),
    (ROOT/'banco-de-dados/bootstrap-administrator.js', '/run/todo/bootstrap-administrator.js'),
    (ROOT/'banco-de-dados/ensure-application-user.js', '/run/todo/ensure-application-user.js'),
]: mounts += ['--mount', f'type=bind,source={source},target={destination},readonly']
try:
    run('run', '-d', '--rm', '--name', name, '--network', 'none', '--memory', '448m', '--mount', f'type=volume,source={name},target=/data/db', *mounts, '--entrypoint', 'mongod', 'todo-mongo:local', '--auth', '--bind_ip', '127.0.0.1', '--wiredTigerCacheSizeGB', '0.256')
    for _ in range(30):
        if mongo('--eval', 'quit(db.adminCommand({ping:1}).ok?0:1)', allow_failure=True).returncode == 0: break
        time.sleep(1)
    admin_auth = "const fs=require('fs'); db.getSiblingDB('admin').auth('administrator',fs.readFileSync('/run/secrets/mongo_root_password','utf8').trim());"
    assert mongo('--eval', admin_auth, allow_failure=True).returncode != 0
    assert 'created' in mongo('/run/todo/bootstrap-administrator.js').stdout
    assert 'created' in mongo('/run/todo/ensure-application-user.js').stdout
    assert 'existing' in mongo('/run/todo/ensure-application-user.js').stdout
    assert mongo('/run/todo/bootstrap-administrator.js', allow_failure=True).returncode != 0
    assert mongo('--eval', admin_auth + "print(db.getSiblingDB('todo-app').todos.countDocuments({}));").stdout.strip().endswith('3')
    limited = "const fs=require('fs'); db.getSiblingDB('todo-app').auth('todo',fs.readFileSync('/run/secrets/mongo_app_password','utf8').trim()); try{db.getSiblingDB('admin').getUsers();throw new Error('Unexpected administrator access');}catch(e){if(e.code!==13)throw e;print('limited');}"
    assert 'limited' in mongo('--eval', limited).stdout
    result = {'passed': True, 'cloud_test': False, 'database': 'real isolated MongoDB with authentication enabled', 'checks': ['missing initial administrator recovered through localhost exception', 'application user created with readWrite only', 'second execution unchanged', 'existing administrator reset refused', 'three demo documents preserved', 'application user cannot administer users'], 'production_volume_mounted': False}
    (ROOT/'docs/evidencias/mongo-bootstrap-recovery.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
finally:
    assert name.startswith('todo-bootstrap-recovery-')
    run('rm', '-f', name, allow_failure=True)
    run('volume', 'rm', name, allow_failure=True)
