"""HTTP/WebSocket contract of the local console (no cluster required)."""
import ipaddress
import threading

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import app as console

ORIGIN = {'Origin': 'http://127.0.0.1:8765'}
# TestClient websockets ignore base_url and send Host: testserver.
WS_HOST = {'Host': '127.0.0.1:8765'}


KIND_NETS = (ipaddress.ip_network('172.19.0.0/16'), ipaddress.ip_network('fc00:f853:ccd:e793::/64'))


@pytest.fixture(autouse=True)
def kind_network(monkeypatch):
    monkeypatch.setattr(console, 'lab_networks', lambda: KIND_NETS)


@pytest.fixture
def client():
    # The browser reaches the console through the published port, i.e. from the Docker gateway.
    return TestClient(console.app, base_url='http://127.0.0.1:8765', client=('172.20.0.1', 50000))


@pytest.fixture
def lab_peer():
    """A lab terminal container or Pod: same forged headers, but a kind source address."""
    return TestClient(console.app, base_url='http://127.0.0.1:8765', client=('172.19.0.7', 40000))


def test_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['mode'] == 'LOCAL_REAL_KUBERNETES'


def test_security_headers(client):
    r = client.get('/api/health')
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert r.headers['Cache-Control'] == 'no-store'


def test_rejects_foreign_host_header():
    remote = TestClient(console.app, base_url='http://evil.example', client=('172.20.0.1', 1))
    assert remote.get('/api/health').status_code == 400


@pytest.mark.parametrize('day', range(1, 21))
def test_every_day_serves_five_exercises(client, day):
    r = client.get(f'/api/day/{day}')
    assert r.status_code == 200
    body = r.json()
    assert body['namespace'] == f'cka-d{day:02d}'
    assert body['markdown'].count('## Exercise ') == 5


@pytest.mark.parametrize('day', [0, 21, 99])
def test_day_out_of_range(client, day):
    assert client.get(f'/api/day/{day}').status_code == 400


@pytest.mark.parametrize('headers', [{}, {'Origin': 'http://evil.example'}, {'Origin': 'http://localhost:8765'}])
def test_actions_require_same_origin(client, headers):
    r = client.post('/api/action', json={'action': 'doctor', 'day': 1}, headers=headers)
    assert r.status_code == 403


@pytest.mark.parametrize('payload', [
    {'action': 'rm -rf /', 'day': 1},
    {'action': 'setup', 'day': 21},
    {'action': 'setup', 'day': 0},
])
def test_action_allow_list(client, payload):
    assert client.post('/api/action', json=payload, headers=ORIGIN).status_code == 422


def test_lab_actions_refused_without_verified_cluster(client, monkeypatch):
    monkeypatch.setattr(console, 'expected_context', lambda: False)
    for action in ('setup', 'verify', 'cleanup'):
        r = client.post('/api/action', json={'action': action, 'day': 3}, headers=ORIGIN)
        assert r.status_code == 412, action
    assert not console._busy.locked()


def test_only_one_action_at_a_time(client, monkeypatch):
    release = threading.Event()

    def blocking_job(job, args):
        release.wait(5)
        job['state'] = 'finished'
        console._busy.release()

    monkeypatch.setattr(console, 'launch_job', blocking_job)
    first = client.post('/api/action', json={'action': 'doctor', 'day': 1}, headers=ORIGIN)
    second = client.post('/api/action', json={'action': 'doctor', 'day': 1}, headers=ORIGIN)
    release.set()
    assert first.status_code == 200
    assert second.status_code == 409
    job = client.get(f"/api/job/{first.json()['id']}").json()
    assert job['action'] == 'doctor'


@pytest.mark.parametrize('job_id', ['nope', '../../etc', 'aaaaaaaaaaaa'])
def test_unknown_job(client, job_id):
    assert client.get(f'/api/job/{job_id}').status_code == 404


def test_resources_report_disconnected_instead_of_empty(client, monkeypatch):
    def broken(*args):
        raise RuntimeError('connection refused')
    monkeypatch.setattr(console, 'objects', broken)
    body = client.get('/api/resources/2').json()
    assert body['connected'] is False
    assert 'connection refused' in body['error']


@pytest.mark.parametrize('action', ['setup', 'verify', 'cleanup'])
def test_action_scripts_exist_for_every_day(action):
    for day in range(1, 21):
        args = console.command_for(console.Action(action=action, day=day))
        assert args[0] == 'bash'
        assert console.ROOT.joinpath(args[1]).is_file()


def test_terminal_requires_container_runtime(monkeypatch):
    monkeypatch.delenv('CKA_CONTAINER', raising=False)
    with pytest.raises(RuntimeError):
        console.terminal_command(1, '/lab/x', 'cka-terminal-abc')


def test_terminal_container_is_isolated(monkeypatch):
    monkeypatch.setenv('CKA_CONTAINER', '1')
    args = console.terminal_command(4, '/lab/cka-session-x', 'cka-terminal-abc')
    joined = ' '.join(args)
    assert '--cap-drop=ALL' in args
    assert '--security-opt=no-new-privileges' in args
    assert 'docker.sock' not in joined, 'terminal must never get the Docker socket'
    assert 'cka-kit-config:/lab:ro' in args
    assert 'KUBECONFIG=/lab/cka-session-x' in args
    assert 'CKA_NS=cka-d04' in args
    assert 'cka-kit.terminal=1' in args, 'label lets the console reap orphaned shells on restart'


def test_terminal_websocket_rejects_foreign_origin(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect('/ws/terminal/1', headers={**WS_HOST, 'Origin': 'http://evil.example'}) as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_terminal_websocket_rejects_bad_day(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect('/ws/terminal/21', headers={**WS_HOST, **ORIGIN}) as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_lab_workloads_cannot_call_the_api_even_with_forged_headers(lab_peer):
    """Regression: a terminal on the kind network could POST /api/action by spoofing Host/Origin."""
    assert lab_peer.get('/api/health').status_code == 403
    r = lab_peer.post('/api/action', json={'action': 'verify', 'day': 11},
                      headers={'Host': 'localhost:8765', 'Origin': 'http://localhost:8765'})
    assert r.status_code == 403
    assert not console._busy.locked()


def test_lab_workloads_cannot_open_terminals(lab_peer):
    with pytest.raises(WebSocketDisconnect) as exc:
        with lab_peer.websocket_connect('/ws/terminal/1', headers={**WS_HOST, **ORIGIN}) as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_terminal_cap_is_enforced(client, monkeypatch):
    monkeypatch.setattr(console, '_terminals', {f'cka-terminal-{i}' for i in range(console.MAX_TERMINALS)})
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect('/ws/terminal/1', headers={**WS_HOST, **ORIGIN}) as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_reaper_retries_until_container_gone(monkeypatch):
    calls = []
    listings = iter(['abc123\n', ''])

    def fake_cli(args, timeout=9, env=None):
        calls.append(args[:2])
        if args[:2] == ['docker', 'ps']:
            return {'ok': True, 'stdout': next(listings), 'stderr': '', 'code': 0}
        return {'ok': True, 'stdout': '', 'stderr': '', 'code': 0}
    monkeypatch.setattr(console, 'cli', fake_cli)
    assert console.reap_terminal_container('cka-terminal-x', delay=0) is True
    assert calls.count(['docker', 'rm']) == 2
