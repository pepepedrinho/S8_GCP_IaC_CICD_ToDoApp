"""Exercise the SSH wrapper with real binary pipes and pre-connection failures."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='todo-ssh-test-') as directory:
    folder = pathlib.Path(directory)
    fake = folder / 'gcloud'
    fake.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
counter = pathlib.Path(os.environ['TODO_TEST_COUNTER'])
attempt = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(attempt))
if os.environ.get('TODO_TEST_DENIED'):
    sys.stderr.write('Permission denied (publickey).')
    sys.exit(255)
if attempt < 3:
    sys.stderr.write('ERROR: (gcloud.compute.ssh) ABORTED: Multiple concurrent mutations were attempted. Please retry the request.')
    sys.exit(1)
sys.stdout.buffer.write(sys.stdin.buffer.read())
''', encoding='utf-8')
    fake.chmod(0o700)
    counter = folder / 'attempts'
    env = os.environ.copy()
    env.update(PATH=str(folder) + os.pathsep + env['PATH'], TODO_TEST_COUNTER=str(counter))
    command = [sys.executable, str(root / 'infra/ansible/gcloud-ssh.py'), 'todo-db', 'cat']
    payload = bytes(range(256)) * 4096
    result = subprocess.run(command, input=payload, capture_output=True, env=env, timeout=30)
    assert result.returncode == 0 and result.stdout == payload, (result.returncode, result.stderr)
    assert counter.read_text() == '3'
    counter.unlink()
    env['TODO_TEST_DENIED'] = '1'
    result = subprocess.run(command, input=payload, capture_output=True, env=env, timeout=10)
    assert result.returncode == 255 and counter.read_text() == '1'
    evidence = {'passed': True, 'binary_pipe_bytes': len(payload), 'pre_ssh_conflict_attempts': 3, 'permission_error_attempts': 1}
    (root / 'docs/evidencias/ssh-transport.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps(evidence))
