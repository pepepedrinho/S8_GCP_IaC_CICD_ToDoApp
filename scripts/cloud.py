#!/usr/bin/env python3
"""Operations restricted to the new academic project; never evaluates user shell input."""
import argparse
import json
import os
import pathlib
import secrets
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local'
PROJECT = 'triodelicia-mensal4-2026'
ZONE = 'us-central1-a'
GCLOUD = shutil.which('gcloud') or 'gcloud'
os.environ.update(CLOUDSDK_CORE_DISABLE_PROMPTS='1', CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK='1', CLOUDSDK_CORE_DISABLE_FILE_LOGGING='1')

def gcloud(*args, json_output=False):
    command = [GCLOUD, *args, '--project=' + PROJECT, '--quiet']
    if json_output: command.append('--format=json')
    r = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
    if r.returncode: raise RuntimeError('gcloud failed: ' + ' '.join(args[:3]) + '\n' + r.stderr[:1800])
    return json.loads(r.stdout) if json_output else r.stdout.strip()

def instances(allow_missing=False):
    found = {}
    for name in ('todo-app', 'todo-db'):
        try:
            found[name] = gcloud('compute', 'instances', 'describe', name, '--zone=' + ZONE, json_output=True)
        except RuntimeError as error:
            if not allow_missing or 'was not found' not in str(error): raise
    return found

def ssh(name, command):
    key = PRIVATE / 'ssh' / 'id_ed25519'
    key.parent.mkdir(parents=True, exist_ok=True)
    if not key.exists(): subprocess.run(['ssh-keygen', '-t', 'ed25519', '-f', str(key), '-N', ''], check=True, capture_output=True)
    return gcloud('compute', 'ssh', name, '--zone=' + ZONE, '--tunnel-through-iap', '--ssh-key-file=' + str(key), '--ssh-key-expire-after=1h', '--command=' + command)

def snapshot(allow_missing=False):
    data = instances(allow_missing)
    summary = {}
    for name in ('todo-app', 'todo-db'):
        if name not in data: summary[name] = {'status': 'NOT_CREATED', 'public_ip': None}
    for name, vm in data.items():
        scheduling = vm['scheduling']
        assert vm['machineType'].endswith('/e2-micro')
        assert int(scheduling['maxRunDuration']['seconds']) <= 21600
        assert scheduling['instanceTerminationAction'] == 'STOP'
        assert not scheduling['automaticRestart']
        configs = vm['networkInterfaces'][0].get('accessConfigs', [])
        if name == 'todo-db': assert not configs
        summary[name] = {'status': vm['status'], 'machine_type': 'e2-micro', 'max_run_seconds': int(scheduling['maxRunDuration']['seconds']), 'termination_action': scheduling['instanceTerminationAction'], 'termination_timestamp': scheduling.get('terminationTimestamp'), 'public_ip': configs[0].get('natIP') if configs else None}
    app_ip = summary['todo-app']['public_ip']
    summary['url'] = 'https://todo-' + app_ip.replace('.', '-') + '.sslip.io' if app_ip else None
    return summary

def prepare():
    PRIVATE.mkdir(exist_ok=True)
    for name in ('todo-app', 'todo-db'):
        for attempt in range(30):
            try: ssh(name, 'true'); break
            except RuntimeError:
                if attempt == 29: raise
                time.sleep(5)
    profile = gcloud('compute', 'os-login', 'describe-profile', json_output=True)
    user = profile['posixAccounts'][0]['username']
    hosts = {}
    for name in ('todo-app', 'todo-db'):
        hosts[name] = {
            'ansible_user': user, 'ansible_host': name,
            'ansible_ssh_private_key_file': str(PRIVATE / 'ssh' / 'id_ed25519'),
            'ansible_ssh_executable': str(ROOT / 'infra/ansible/gcloud-ssh.py'),
            'ansible_ssh_transfer_method': 'piped',
        }
    inventory = {'all': {'children': {'app': {'hosts': {'todo-app': hosts['todo-app']}}, 'database': {'hosts': {'todo-db': hosts['todo-db']}}}}}
    (PRIVATE / 'inventory.yml').write_text(json.dumps(inventory, indent=2))
    private_config = PRIVATE / 'cloud-secrets.json'
    if not private_config.exists():
        values = {k: os.environ.get(k.upper()) or secrets.token_hex(24) for k in ('mongo_root_password', 'mongo_app_password')}
        private_config.write_text(json.dumps(values)); private_config.chmod(0o600)
    state = snapshot()
    config = {'todo_domain': state['url'].removeprefix('https://')}
    (PRIVATE / 'runtime.json').write_text(json.dumps(config))
    print(json.dumps({'inventory': 'ready', 'url': state['url']}))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['status', 'prepare', 'boot', 'start', 'stop', 'backup', 'restore', 'rollback', 'logs'])
    parser.add_argument('--object', default='')
    args = parser.parse_args()
    if args.operation in ('boot', 'start'):
        for name in ('todo-db', 'todo-app'):
            if gcloud('compute', 'instances', 'describe', name, '--zone=' + ZONE, json_output=True)['status'] != 'RUNNING':
                gcloud('compute', 'instances', 'start', name, '--zone=' + ZONE)
        prepare()
        # A graceful stop deliberately stops containers; unless-stopped does not
        # bring those containers back after a VM reboot.
        if args.operation == 'start':
            ssh('todo-db', 'sudo docker compose -f /opt/todo/compose.yml up -d --pull never --wait --wait-timeout 120')
            ssh('todo-app', 'sudo docker compose --env-file /opt/todo/release.env -f /opt/todo/compose.yml up -d --pull never --wait --wait-timeout 120')
    elif args.operation == 'stop':
        existing = instances(allow_missing=True)
        for name, vm in existing.items():
            if vm['status'] != 'RUNNING': continue
            release = '--env-file /opt/todo/release.env ' if name == 'todo-app' else ''
            try: ssh(name, f'sudo docker compose {release}-f /opt/todo/compose.yml stop')
            except RuntimeError: pass
        # Attempt both stops even if graceful shutdown failed.
        failures = []
        for name in existing:
            try: gcloud('compute', 'instances', 'stop', name, '--zone=' + ZONE)
            except RuntimeError as error: failures.append(str(error))
        state = snapshot(allow_missing=True)
        assert all(state[n]['status'] in ('TERMINATED', 'NOT_CREATED') for n in ('todo-app', 'todo-db')), failures
    elif args.operation == 'prepare': prepare()
    elif args.operation == 'backup': print(ssh('todo-db', 'sudo /opt/todo/bin/backup.sh'))
    elif args.operation == 'rollback': print(ssh('todo-app', 'sudo /opt/todo/bin/deploy-images.sh rollback'))
    elif args.operation == 'logs':
        for name in ('todo-app', 'todo-db'): print(ssh(name, 'sudo docker ps --format "{{.Names}} {{.Status}}"; sudo journalctl -u todo-backup.service -n 10 --no-pager'))
    elif args.operation == 'restore':
        import re
        if not re.fullmatch(r'todo/todo-\d{8}T\d{6}Z\.archive\.gz', args.object): raise ValueError('Invalid backup object')
        command = f"sudo bash -c 'set -e; cd /opt/todo; source backup.env; python3 bin/gcs.py download \"$BACKUP_BUCKET\" {args.object} backups/restore.archive.gz; python3 bin/gcs.py download \"$BACKUP_BUCKET\" {args.object}.json backups/restore.archive.gz.json; python3 bin/verify-backup.py backups/restore.archive.gz'"
        print(ssh('todo-db', command))
    state = snapshot(allow_missing=args.operation == 'stop')
    evidence = ROOT / 'docs' / 'evidencias'; evidence.mkdir(parents=True, exist_ok=True)
    (evidence / ('cloud-' + args.operation + '.json')).write_text(json.dumps(state, indent=2))
    print(json.dumps(state, indent=2))

if __name__ == '__main__': main()
