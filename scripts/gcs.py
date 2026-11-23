#!/usr/bin/env python3
"""Private GCS object access with short-lived VM metadata identity, no key files."""
import argparse
import json
import pathlib
import urllib.parse
import urllib.request

def request(url, method='GET', data=None, headers=None):
    req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['upload', 'download'])
    parser.add_argument('bucket')
    parser.add_argument('object')
    parser.add_argument('path', type=pathlib.Path)
    args = parser.parse_args()
    token = json.loads(request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token', headers={'Metadata-Flavor': 'Google'}))['access_token']
    headers = {'Authorization': 'Bearer ' + token}
    bucket, name = urllib.parse.quote(args.bucket, safe=''), urllib.parse.quote(args.object, safe='')
    if args.operation == 'upload':
        headers['Content-Type'] = 'application/octet-stream'
        request(f'https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o?uploadType=media&name={name}', 'POST', args.path.read_bytes(), headers)
    else:
        args.path.write_bytes(request(f'https://storage.googleapis.com/storage/v1/b/{bucket}/o/{name}?alt=media', headers=headers))
    print(json.dumps({'operation': args.operation, 'object': args.object, 'status': 'ok'}))

if __name__ == '__main__':
    main()
