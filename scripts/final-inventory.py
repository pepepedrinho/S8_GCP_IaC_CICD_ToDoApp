"""Read-only final inventory of the one allowed project, without billing account IDs."""
import datetime
import json
import urllib.parse
import urllib.request
from cloud import gcloud, ROOT

project = gcloud('projects', 'describe', 'triodelicia-mensal4-2026', json_output=True)
billing = gcloud('billing', 'projects', 'describe', 'triodelicia-mensal4-2026', json_output=True)
services = gcloud('services', 'list', '--enabled', json_output=True)
enabled = sorted(item['config']['name'] for item in services)
result = {
    'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'project_id': project['projectId'],
    'project_state': project['lifecycleState'],
    'billing_enabled': billing.get('billingEnabled', False),
    'enabled_apis': enabled,
    'bootstrap_apply_record_present': (ROOT / '.local' / 'bootstrap-outputs.json').exists(),
    'compute_inventory': None,
    'disks': None,
    'reserved_addresses': None,
    'buckets': None,
}
if 'compute.googleapis.com' in enabled:
    vms = gcloud('compute', 'instances', 'list', json_output=True)
    result['compute_inventory'] = [{
        'name': vm['name'], 'status': vm['status'],
        'machine_type': vm['machineType'].split('/')[-1],
        'zone': vm['zone'].split('/')[-1],
        'created': vm.get('creationTimestamp'), 'last_start': vm.get('lastStartTimestamp'),
        'last_stop': vm.get('lastStopTimestamp'), 'scheduling': vm['scheduling'],
        'private_ip': vm['networkInterfaces'][0]['networkIP'],
        'public_ips': [a.get('natIP') for n in vm['networkInterfaces'] for a in n.get('accessConfigs', []) if a.get('natIP')],
    } for vm in vms]
    result['all_vms_terminated'] = len(vms) == 2 and all(vm['status'] == 'TERMINATED' for vm in vms)
    result['disks'] = [{'name': d['name'], 'size_gb': d['sizeGb'], 'type': d['type'].split('/')[-1], 'zone': d['zone'].split('/')[-1], 'status': d['status']} for d in gcloud('compute', 'disks', 'list', json_output=True)]
    result['reserved_addresses'] = [{'name': a['name'], 'status': a['status']} for a in gcloud('compute', 'addresses', 'list', json_output=True)]
    result['routers'] = [r['name'] for r in gcloud('compute', 'routers', 'list', json_output=True)]
    result['forwarding_rules'] = [r['name'] for r in gcloud('compute', 'forwarding-rules', 'list', json_output=True)]
    result['networks'] = [n['name'] for n in gcloud('compute', 'networks', 'list', json_output=True)]
    result['firewalls'] = [{'name': f['name'], 'network': f['network'].split('/')[-1], 'source_ranges': f.get('sourceRanges'), 'target_tags': f.get('targetTags'), 'allowed': f.get('allowed')} for f in gcloud('compute', 'firewall-rules', 'list', json_output=True)]
    result['instance_operations'] = [{
        'instance': o['targetLink'].split('/')[-1], 'operation': o['operationType'],
        'started': o.get('startTime', o.get('insertTime')), 'finished': o.get('endTime'),
        'status': o['status'], 'failed': bool(o.get('error')),
    } for o in gcloud('compute', 'operations', 'list', json_output=True)
        if o.get('targetLink', '').split('/')[-1] in ('todo-app', 'todo-db') and o['operationType'] in ('insert', 'start', 'stop')]
else:
    result['compute_query_note'] = 'Compute API is disabled; inventory was not queried.'
if 'storage.googleapis.com' in enabled:
    result['buckets'] = []
    token = gcloud('auth', 'print-access-token')
    for bucket in gcloud('storage', 'buckets', 'list', json_output=True):
        name = bucket['name']
        details = gcloud('storage', 'buckets', 'describe', 'gs://' + name, json_output=True)
        objects = []
        page = ''
        while True:
            url = 'https://storage.googleapis.com/storage/v1/b/' + urllib.parse.quote(name, safe='') + '/o?versions=true'
            if page: url += '&pageToken=' + urllib.parse.quote(page, safe='')
            request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
            with urllib.request.urlopen(request, timeout=30) as response: data = json.load(response)
            objects.extend({'name': o['name'], 'size_bytes': int(o['size']), 'generation': o['generation'], 'created': o['timeCreated']} for o in data.get('items', []))
            page = data.get('nextPageToken')
            if not page: break
        result['buckets'].append({'name': name, 'location': details['location'], 'storage_class': details['default_storage_class'], 'public_access_prevention': details['public_access_prevention'], 'uniform_access': details['uniform_bucket_level_access'], 'versioning_enabled': details.get('versioning_enabled', False), 'retention_policy': details.get('retention_policy'), 'lifecycle': details.get('lifecycle_config'), 'total_version_bytes': sum(o['size_bytes'] for o in objects), 'objects_all_versions': objects})
else:
    result['storage_query_note'] = 'Storage API is disabled; inventory was not queried.'
target = ROOT / 'docs' / 'evidencias' / 'cloud-final.json'
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
