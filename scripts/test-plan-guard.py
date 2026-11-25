"""Verify cost/security boundaries by mutating actual reviewed Terraform plans."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
base = json.loads((root / 'docs/evidencias/terraform-main-plan.json').read_text(encoding='utf-8'))
def resource(plan, address):
    return next(r for r in plan['resource_changes'] if r['address'] == address)
def after(plan, address):
    return resource(plan, address)['change']['after']
app = 'google_compute_instance.vm["app"]'
database = 'google_compute_instance.vm["db"]'
disk = 'google_compute_disk.data'
def extra_disk(plan):
    extra = copy.deepcopy(resource(plan, disk))
    extra['address'] = 'google_compute_disk.extra'
    extra['change']['after']['name'] = 'unexpected-paid-disk'
    plan['resource_changes'].append(extra)
def deletion(plan):
    resource(plan, disk)['change'].update(actions=['delete'], after=None)
cases = {
    'additional disk': extra_disk,
    'unapproved region': lambda p: after(p, app).update(zone='europe-west1-b'),
    'oversized data disk': lambda p: after(p, disk).update(size=1000),
    'SSD boot disk': lambda p: after(p, app)['boot_disk'][0]['initialize_params'][0].update(type='pd-ssd'),
    'public SSH': lambda p: after(p, 'google_compute_firewall.iap').update(source_ranges=['0.0.0.0/0']),
    'public database address': lambda p: after(p, database)['network_interface'][0].update(access_config=[{}]),
    'automatic restart': lambda p: after(p, app)['scheduling'][0].update(automatic_restart=True),
    'runtime beyond six hours': lambda p: after(p, app)['scheduling'][0]['max_run_duration'][0].update(seconds=25200),
    'unapproved service': lambda p: resource(p, disk).update(type='google_sql_database_instance'),
    'destruction through normal apply': deletion,
}
accepted, rejected = [], []
local = root / '.local'
local.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='plan-guard-test-', dir=local) as directory:
    assert pathlib.Path(directory).resolve().is_relative_to(local.resolve())
    path = pathlib.Path(directory) / 'plan.json'
    def run(plan):
        path.write_text(json.dumps(plan), encoding='utf-8')
        return subprocess.run([sys.executable, str(root / 'scripts/check-plan.py'), str(path)], capture_output=True).returncode
    for name in ('terraform-main-plan.json', 'terraform-main-reviewed-plan.json'):
        assert run(json.loads((root / 'docs/evidencias' / name).read_text(encoding='utf-8'))) == 0
        accepted.append(name)
    for name, mutate in cases.items():
        plan = copy.deepcopy(base)
        mutate(plan)
        assert run(plan) != 0, name
        rejected.append(name)
result = {'passed': True, 'accepted_real_plans': accepted, 'rejected_mutations': rejected, 'cloud_resources_changed': False}
(root / 'docs/evidencias/plan-guard.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
