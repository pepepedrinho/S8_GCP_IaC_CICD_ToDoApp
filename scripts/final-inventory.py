"""Read-only final inventory of the one allowed project, without billing account IDs."""
import datetime
import json
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
    'bootstrap_applied': False,
    'compute_inventory': None,
    'disks': None,
    'reserved_addresses': None,
    'buckets': None,
}
if 'compute.googleapis.com' in enabled:
    vms = gcloud('compute', 'instances', 'list', json_output=True)
    result['compute_inventory'] = [{'name': vm['name'], 'status': vm['status']} for vm in vms]
    result['disks'] = [{'name': d['name'], 'size_gb': d['sizeGb']} for d in gcloud('compute', 'disks', 'list', json_output=True)]
    result['reserved_addresses'] = [{'name': a['name'], 'status': a['status']} for a in gcloud('compute', 'addresses', 'list', json_output=True)]
else:
    result['compute_query_note'] = 'Compute API is disabled; no provisioning/apply was performed in this implementation.'
if 'storage.googleapis.com' in enabled:
    result['buckets'] = [b.get('name') for b in gcloud('storage', 'buckets', 'list', json_output=True)]
else:
    result['storage_query_note'] = 'Storage API is disabled; no buckets were applied.'
target = ROOT / 'docs' / 'evidencias' / 'cloud-final.json'
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
