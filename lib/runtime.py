"""Reconnect a recreated console container to kind's independent Docker network."""
import json
import os
from pathlib import Path
import subprocess


def connect():
    if os.environ.get('CKA_CONTAINER') != '1':
        return
    node = subprocess.run(['docker', 'inspect', 'cka-14d-control-plane'], capture_output=True, text=True)
    if node.returncode:
        return
    labels = json.loads(node.stdout)[0]['Config'].get('Labels', {})
    if labels.get('io.x-k8s.kind.cluster') != 'cka-14d':
        raise RuntimeError('REFUSED: named control plane is not a kind lab node')
    hostname = os.environ['HOSTNAME']
    own = json.loads(subprocess.check_output(['docker', 'inspect', hostname]))[0]
    if 'kind' not in own['NetworkSettings']['Networks']:
        subprocess.run(['docker', 'network', 'connect', 'kind', hostname], check=True)
    config = subprocess.check_output(['kind', 'get', 'kubeconfig', '--name', 'cka-14d', '--internal'])
    path = Path(os.environ['KUBECONFIG'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(config)
    path.chmod(0o600)


if __name__ == '__main__':
    connect()
