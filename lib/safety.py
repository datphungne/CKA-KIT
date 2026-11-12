"""Bind automation to the actual named kind cluster, never a context name alone."""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
import yaml

CONTEXT = 'kind-cka-14d'
MAX_DAY = 20  # 14-day bootcamp + topic labs 15..20
CLUSTER = 'cka-14d'

def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=15, check=True)
    return result.stdout

def trusted_config():
    nodes = json.loads(run(['docker', 'inspect', 'cka-14d-control-plane']))
    labels = nodes[0].get('Config', {}).get('Labels', {})
    if labels.get('io.x-k8s.kind.cluster') != CLUSTER or labels.get('io.x-k8s.kind.role') != 'control-plane':
        raise RuntimeError('REFUSED: control plane is not the dedicated kind lab')
    expected = yaml.safe_load(run(['kind', 'get', 'kubeconfig', '--name', CLUSTER, '--internal']))
    actual = json.loads(run(['kubectl', 'config', 'view', '--raw', '--flatten', '-o', 'json']))
    contexts = [c for c in actual.get('contexts', []) if c['name'] == CONTEXT]
    if len(contexts) != 1:
        raise RuntimeError('REFUSED: dedicated lab context missing')
    selected = contexts[0]['context']
    cluster = next(c['cluster'] for c in actual['clusters'] if c['name'] == selected['cluster'])
    reference = expected['clusters'][0]['cluster']
    if cluster.get('certificate-authority-data') != reference.get('certificate-authority-data'):
        raise RuntimeError('REFUSED: lab CA does not match the kind control plane')
    # Use kind-exported credentials, never an arbitrary auth/exec plugin from a host config.
    if os.environ.get('CKA_CONTAINER') != '1':
        expected = yaml.safe_load(run(['kind', 'get', 'kubeconfig', '--name', CLUSTER]))
    expected['current-context'] = CONTEXT
    return expected

def snapshot(day=None):
    config = trusted_config()
    if day is not None:
        if not 1 <= int(day) <= MAX_DAY:
            raise ValueError(f'Day must be 1..{MAX_DAY}')
        config['contexts'][0]['context']['namespace'] = f'cka-d{int(day):02d}'
    directory = '/lab' if os.environ.get('CKA_CONTAINER') == '1' else None
    fd, name = tempfile.mkstemp(prefix='cka-session-', dir=directory)
    with os.fdopen(fd, 'w') as stream:
        json.dump(config, stream)
    return name

if __name__ == '__main__':
    import sys
    try:
        print(snapshot(int(sys.argv[1]) if len(sys.argv) > 1 else None))
    except Exception as exc:
        sys.exit(f'REFUSED: unable to establish dedicated lab identity: {exc}')
