"""Real HTTP CRUD through the same public/frontend origin. Deletes only its own task."""
import argparse
import concurrent.futures
import json
import pathlib
import statistics
import time
import urllib.error
import urllib.request

def call(base, path, method='GET', body=None):
    request = urllib.request.Request(base.rstrip('/') + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status, json.load(response)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--evidence', default='docs/evidencias/smoke.json')
    parser.add_argument('--load', action='store_true')
    args = parser.parse_args()
    base = args.url
    result = {'url': base, 'https_verified': base.startswith('https://'), 'checks': []}
    with urllib.request.urlopen(base, timeout=15) as response:
        assert response.status == 200 and b'<div id="root"' in response.read()
    assert call(base, '/health/ready')[1]['database'] == 'ok'
    result['checks'].append('frontend and database readiness')
    status, todo = call(base, '/todos', 'POST', {'text': f'Acceptance {time.time_ns()}'})
    assert status == 201 and todo['completed'] is False
    path = '/todos/' + todo['_id']
    try:
        assert any(x['_id'] == todo['_id'] for x in call(base, '/todos')[1])
        assert call(base, path, 'PATCH')[1]['completed'] is True
        assert call(base, path, 'PATCH')[1]['completed'] is False
        result['checks'] += ['create', 'list', 'complete', 'reopen']
    finally:
        assert call(base, path, 'DELETE')[0] == 200
    assert not any(x['_id'] == todo['_id'] for x in call(base, '/todos')[1])
    result['checks'].append('delete and reload')
    if args.load:
        def sample(_):
            started = time.monotonic()
            assert call(base, '/todos')[0] == 200
            return time.monotonic() - started
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            timings = list(pool.map(sample, range(100)))
        result['load'] = {'concurrency': 10, 'requests': 100, 'errors': 0, 'p95_seconds': sorted(timings)[94], 'mean_seconds': statistics.mean(timings)}
    result['passed'] = True
    dest = pathlib.Path(args.evidence); dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
