"""Fail closed before apply: only the approved topology, no deletion by normal apply."""
import argparse
import json
import pathlib
parser = argparse.ArgumentParser()
parser.add_argument('plan')
parser.add_argument('--destroy', action='store_true')
args = parser.parse_args()
plan = json.loads(pathlib.Path(args.plan).read_text(encoding='utf-8'))
allowed = {'google_compute_network', 'google_compute_subnetwork', 'google_compute_firewall', 'google_compute_disk', 'google_compute_instance'}
addresses = {
    'google_compute_network.todo', 'google_compute_subnetwork.todo',
    'google_compute_firewall.web', 'google_compute_firewall.iap',
    'google_compute_firewall.mongo', 'google_compute_firewall.packages',
    'google_compute_disk.data',
    'google_compute_instance.vm["app"]', 'google_compute_instance.vm["db"]',
}
seen = set()
vms = []
for item in plan.get('resource_changes', []):
    if item.get('mode') == 'data': continue
    assert item['type'] in allowed, 'Unapproved resource: ' + item['type']
    assert item['address'] in addresses, 'Unapproved resource address: ' + item['address']
    seen.add(item['address'])
    actions = item['change']['actions']
    assert args.destroy or 'delete' not in actions, 'Destructive change requires explicit destroy workflow'
    after = item['change'].get('after')
    if not after: continue
    assert after.get('project', 'triodelicia-mensal4-2026') == 'triodelicia-mensal4-2026'
    if item['type'] == 'google_compute_firewall':
        expected = {
            'todo-web': (['80', '443'], ['0.0.0.0/0'], ['todo-app']),
            'todo-iap-ssh': (['22'], ['35.235.240.0/20'], ['todo-app', 'todo-db']),
            'todo-private-mongo': (['27017'], ['10.42.0.10/32'], ['todo-db']),
            'todo-private-packages': (['3128'], ['10.42.0.20/32'], ['todo-app']),
        }
        ports, sources, targets = expected[after['name']]
        assert len(after['allow']) == 1 and after['allow'][0]['protocol'] == 'tcp'
        assert sorted(after['allow'][0]['ports']) == sorted(ports)
        assert sorted(after['source_ranges']) == sorted(sources)
        assert sorted(after['target_tags']) == sorted(targets)
    if item['type'] == 'google_compute_disk':
        assert after['size'] == 10 and after['type'] == 'pd-standard'
        assert after['name'] == 'todo-mongo-data' and after['zone'].startswith('us-central1-')
    if item['type'] == 'google_compute_network':
        assert after['name'] == 'todo-vpc' and after['auto_create_subnetworks'] is False
    if item['type'] == 'google_compute_subnetwork':
        assert after['name'] == 'todo-subnet' and after['region'] == 'us-central1'
        assert after['ip_cidr_range'] == '10.42.0.0/24'
    if item['type'] == 'google_compute_instance':
        vms.append(after)
        assert after['machine_type'] == 'e2-micro'
        assert after['zone'].startswith('us-central1-')
        schedule = after['scheduling'][0]
        assert schedule['max_run_duration'][0]['seconds'] <= 21600
        assert schedule['instance_termination_action'] == 'STOP' and not schedule['automatic_restart']
        assert after['boot_disk'][0]['initialize_params'][0]['size'] == 10
        assert after['boot_disk'][0]['initialize_params'][0]['type'] == 'pd-standard'
        if after['name'] == 'todo-db': assert not after['network_interface'][0]['access_config']
        elif after['name'] == 'todo-app': assert len(after['network_interface'][0]['access_config']) == 1
        else: raise AssertionError('Unexpected VM')
assert args.destroy or len(vms) == 2, 'Exactly two VMs are required'
assert args.destroy or seen == addresses, 'The complete approved topology is required'
print('Approved topology, runtime guard and deletion policy verified.')
