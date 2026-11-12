"""End-to-end lab lifecycle against the running console and a real kind cluster.

Opt-in because it takes several minutes and needs Docker:
    docker compose up -d --build        # console on 127.0.0.1:8765
    CKA_INTEGRATION=1 python -m pytest tests/test_integration.py -v
The cluster must already exist (click "Create cluster" once, or POST action=create-cluster).
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

import pytest

BASE = os.environ.get('CKA_URL', 'http://127.0.0.1:8765')
HEADERS = {'Content-Type': 'application/json', 'Origin': BASE}

pytestmark = pytest.mark.skipif(os.environ.get('CKA_INTEGRATION') != '1', reason='set CKA_INTEGRATION=1')


def call(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HEADERS if data else {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def run_action(action, day, timeout=900):
    deadline = time.time() + 60
    while True:  # another action may still be finishing
        try:
            job_id = call('/api/action', {'action': action, 'day': day})['id']
            break
        except urllib.error.HTTPError as exc:
            if exc.code != 409 or time.time() > deadline:
                raise
            time.sleep(3)
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = call(f'/api/job/{job_id}')
        if job['state'] == 'finished':
            return job
        time.sleep(3)
    raise TimeoutError(f'{action} day {day} did not finish')


@pytest.fixture(scope='module', autouse=True)
def cluster_ready():
    status = call('/api/status')
    if not status['ready']:
        pytest.skip('kind-cka-14d is not ready; create the cluster first')
    assert status['readyNodes'] == status['nodes'] == 3


def namespace_pods(day):
    return call(f'/api/resources/{day}')


@pytest.mark.parametrize('day', range(1, 21))
def test_day_lifecycle(day):
    setup = run_action('setup', day)
    assert setup['code'] == 0, setup['output'][-3000:]

    seeded = namespace_pods(day)
    assert seeded['connected'] is True

    verify = run_action('verify', day)
    assert 'Summary:' in verify['output'], verify['output'][-3000:]
    results = re.findall(rf'\[(PASS|FAIL|MANUAL)\]\s+{day:02d}\.(\d+)', verify['output'])
    assert len(results) == 5, verify['output'][-3000:]
    assert 'checker exception' not in verify['output'], verify['output'][-3000:]
    # Freshly seeded labs are unsolved: nothing may be auto-marked as passed.
    assert all(state != 'PASS' for state, _ in results), results

    cleanup = run_action('cleanup', day)
    assert cleanup['code'] == 0, cleanup['output'][-3000:]
    after = namespace_pods(day)
    assert after['connected'] is True
    assert after['pods'] == [] and after['deployments'] == []


def docker(*args, stdin=None):
    import subprocess
    env = {**os.environ, 'MSYS_NO_PATHCONV': '1'}
    return subprocess.run(['docker', *args], input=stdin, capture_output=True, text=True, timeout=120, env=env)


def test_lab_network_cannot_reach_console():
    """A terminal/Pod on the kind network must not drive the console, even with forged headers."""
    ip = docker('inspect', 'cka-kit-console-1', '-f', '{{(index .NetworkSettings.Networks "kind").IPAddress}}').stdout.strip()
    probe = docker('run', '--rm', '--network', 'kind', 'cka-kit:local', 'curl', '-sS', '-m', '5', '-o', '/dev/null',
                   '-w', '%{http_code}', '-X', 'POST', '-H', 'Host: localhost:8765', '-H', 'Origin: http://localhost:8765',
                   '-H', 'Content-Type: application/json', '-d', '{"action":"doctor","day":1}', f'http://{ip}:8765/api/action')
    assert probe.stdout == '403', probe


MALICIOUS_KUBECONFIG = '''apiVersion: v1
kind: Config
current-context: x
clusters: [{name: x, cluster: {server: "https://cka-14d-control-plane:6443", insecure-skip-tls-verify: true}}]
contexts: [{name: x, context: {cluster: x, user: x}}]
users:
- name: x
  user:
    exec: {apiVersion: client.authentication.k8s.io/v1, command: touch, args: [/tmp/PWNED_BY_KUBECONFIG], interactiveMode: Never}
'''


def test_grader_never_executes_learner_kubeconfig_plugins():
    target = '/workspace/answers/day11-kubeconfig.yaml'
    assert docker('exec', 'cka-kit-console-1', 'test', '-e', target).returncode != 0, 'refusing to overwrite a real answer'
    assert docker('exec', '-i', 'cka-kit-console-1', 'sh', '-c', f'cat > {target}', stdin=MALICIOUS_KUBECONFIG).returncode == 0
    try:
        verify = run_action('verify', 11)
        assert re.search(r'\[FAIL\]\s+11\.4', verify['output'])
        assert docker('exec', 'cka-kit-console-1', 'test', '-e', '/tmp/PWNED_BY_KUBECONFIG').returncode != 0
    finally:
        docker('exec', 'cka-kit-console-1', 'rm', '-f', target, '/tmp/PWNED_BY_KUBECONFIG')
