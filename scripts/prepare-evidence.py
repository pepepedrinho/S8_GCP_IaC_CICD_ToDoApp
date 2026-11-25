"""Discard historical copies only on an Actions runner before collecting a run."""
import datetime
import json
import os
import pathlib
import sys

if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise SystemExit('This cleanup is restricted to disposable Actions checkouts')
kind = sys.argv[1]
names = {
    'deploy': ['cloud-boot', 'cloud-dns', 'cloud-status', 'cloud-stop', 'cloud-diagnostics', 'gcp-smoke', 'gcp-acceptance', 'gcp-recovery'],
    'operate': ['cloud-start', 'cloud-dns', 'cloud-stop', 'cloud-status', 'cloud-boot', 'cloud-logs', 'cloud-diagnostics', 'cloud-backup', 'cloud-restore', 'cloud-rollback', 'reactivation-smoke', 'gcp-acceptance', 'gcp-recovery', 'gcp-operations-idempotence'],
    'infra': ['cloud-status', 'cloud-stop'],
}[kind]
folder = pathlib.Path(__file__).resolve().parents[1] / 'docs/evidencias'
folder.mkdir(parents=True, exist_ok=True)
for name in names:
    (folder / (name + '.json')).unlink(missing_ok=True)
context = {
    'run_url': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    'source_commit': os.environ['GITHUB_SHA'],
    'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'kind': kind,
    'operation': os.environ.get('OPERATION'),
    'image_commit': os.environ.get('IMAGE_COMMIT'),
    'comparison_commit': os.environ.get('COMPARISON_COMMIT'),
    'recovery_only': os.environ.get('OPERATION') == 'recovery',
}
(folder / (kind + '-context.json')).write_text(json.dumps(context, indent=2), encoding='utf-8')
