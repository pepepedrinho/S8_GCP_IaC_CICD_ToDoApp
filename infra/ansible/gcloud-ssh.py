#!/usr/bin/env python3
"""Ansible SSH transport through gcloud's automatically renewed OS Login certs.

gcloud handles IAP, host identity and the federated identity's temporary SSH
certificate for every connection. Piped transfer keeps binary data on stdout.
"""
import pathlib
import shutil
import subprocess
import sys
import time

arguments = sys.argv[1:]
hosts = [(i, arg) for i, arg in enumerate(arguments) if arg in ('todo-app', 'todo-db')]
if len(hosts) != 1:
    raise SystemExit('Only the two approved instance names are accepted')
index, host = hosts[0]
remote_command = ' '.join(arguments[index + 1:])
if not remote_command: raise SystemExit(0)
root = pathlib.Path(__file__).resolve().parents[2]
command = [
    shutil.which('gcloud') or 'gcloud', 'compute', 'ssh', host,
    '--project=triodelicia-mensal4-2026', '--zone=us-central1-a',
    '--tunnel-through-iap', '--quiet',
    '--ssh-key-file=' + str(root / '.local/ssh/id_ed25519'),
    '--ssh-key-expire-after=1h',
    '--ssh-flag=-oConnectTimeout=30', '--ssh-flag=-oServerAliveInterval=15',
    '--ssh-flag=-oServerAliveCountMax=4', '--command=' + remote_command,
]
# OS Login can reject consecutive key imports while its preceding mutation is
# settling. This exact error precedes SSH, so the remote command and stdin have
# not been consumed. Keep stdout inherited for binary piped file transfers.
for attempt in range(4):
    result = subprocess.run(command, stderr=subprocess.PIPE)
    if result.returncode and b'ABORTED: Multiple concurrent mutations were attempted.' in result.stderr and attempt < 3:
        time.sleep(2 ** (attempt + 1))
        continue
    sys.stderr.buffer.write(result.stderr)
    raise SystemExit(result.returncode)
