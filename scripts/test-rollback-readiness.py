"""Real HTTP regression for rollback waiting for a newly started frontend."""
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import threading

root = pathlib.Path(__file__).resolve().parents[1]
class Handler(http.server.BaseHTTPRequestHandler):
    requests = 0
    permanent_failure = False
    def do_GET(self):
        Handler.requests += 1
        self.send_response(503 if Handler.permanent_failure or Handler.requests < 3 else 200)
        self.end_headers()
    def log_message(self, *_):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
local = root / '.local'
local.mkdir(exist_ok=True)
try:
    with tempfile.TemporaryDirectory(prefix='rollback-http-test-', dir=local) as directory:
        folder = pathlib.Path(directory)
        assert folder.resolve().is_relative_to(local.resolve())
        docker = folder / 'docker'
        docker.write_text('#!/bin/sh\nexit 0\n')
        docker.chmod(0o700)
        curl = folder / 'curl'
        real_curl = shutil.which('curl')
        curl.write_text('#!/usr/bin/env python3\nimport os,sys\n'
                        + f"args=[a.replace('127.0.0.1:8080','127.0.0.1:{server.server_port}') for a in sys.argv[1:]]\n"
                        + f'os.execv({real_curl!r},[{real_curl!r}]+args)\n')
        curl.chmod(0o700)
        env = dict(os.environ, PATH=str(folder)+os.pathsep+os.environ['PATH'], TODO_ROOT=str(folder))
        (folder / 'release.env').write_text('APP_VERSION=new\n')
        (folder / 'release.previous.env').write_text('APP_VERSION=previous\n')
        command = ['bash', str(root / 'scripts/deploy-images.sh'), 'rollback']
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0 and 'rolled_back' in result.stdout, result.stderr
        assert Handler.requests == 3 and (folder / 'release.env').read_text() == 'APP_VERSION=previous\n'
        Handler.requests = 0
        Handler.permanent_failure = True
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=35)
        assert result.returncode != 0 and 'rolled_back' not in result.stdout
        evidence = {'passed': True, 'scope': 'real HTTP with simulated Docker startup', 'transient_503_requests_before_success': 2, 'permanent_503_rejected': True, 'cloud_test': False}
        (root / 'docs/evidencias/rollback-readiness.json').write_text(json.dumps(evidence, indent=2))
        print(json.dumps(evidence))
finally:
    server.shutdown()
    server.server_close()
