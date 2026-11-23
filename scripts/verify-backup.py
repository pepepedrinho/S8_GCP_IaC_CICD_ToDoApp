#!/usr/bin/env python3
import hashlib
import json
import pathlib
import subprocess
import sys
archive = pathlib.Path(sys.argv[1]).resolve()
manifest = json.loads(pathlib.Path(str(archive) + '.json').read_text())
assert manifest['validated'] is True
assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256']
subprocess.run([str(pathlib.Path(__file__).with_name('restore-isolated.sh')), str(archive), manifest['data_sha256']], check=True)
