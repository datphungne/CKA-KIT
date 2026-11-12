"""lib/safety.py must only ever hand out credentials for the dedicated kind lab."""
import json
import tempfile

import pytest
import yaml

import safety

CA = 'TEFCLUNB'


def kind_config(server='https://cka-14d-control-plane:6443', ca=CA):
    return {
        'apiVersion': 'v1', 'kind': 'Config', 'current-context': 'kind-cka-14d',
        'clusters': [{'name': 'kind-cka-14d', 'cluster': {'server': server, 'certificate-authority-data': ca}}],
        'contexts': [{'name': 'kind-cka-14d', 'context': {'cluster': 'kind-cka-14d', 'user': 'kind-cka-14d'}}],
        'users': [{'name': 'kind-cka-14d', 'user': {'client-certificate-data': 'x', 'client-key-data': 'y'}}],
    }


def fake_runner(labels=None, active=None, internal=None):
    labels = labels if labels is not None else {'io.x-k8s.kind.cluster': 'cka-14d', 'io.x-k8s.kind.role': 'control-plane'}
    active = active if active is not None else kind_config()
    internal = internal if internal is not None else kind_config()

    def run(args):
        if args[:2] == ['docker', 'inspect']:
            return json.dumps([{'Config': {'Labels': labels}}])
        if args[:3] == ['kind', 'get', 'kubeconfig']:
            server = 'https://cka-14d-control-plane:6443' if '--internal' in args else 'https://127.0.0.1:41234'
            return yaml.safe_dump({**internal, 'clusters': [{**internal['clusters'][0], 'cluster': {**internal['clusters'][0]['cluster'], 'server': server}}]})
        if args[:3] == ['kubectl', 'config', 'view']:
            return json.dumps(active)
        raise AssertionError(f'unexpected command {args}')
    return run


@pytest.fixture(autouse=True)
def in_container(monkeypatch, tmp_path):
    """Simulate the console container; write snapshots to tmp instead of /lab."""
    monkeypatch.setenv('CKA_CONTAINER', '1')
    real_mkstemp = tempfile.mkstemp
    monkeypatch.setattr(safety.tempfile, 'mkstemp', lambda prefix, dir=None: real_mkstemp(prefix=prefix, dir=tmp_path))


def test_accepts_matching_kind_lab(monkeypatch):
    monkeypatch.setattr(safety, 'run', fake_runner())
    config = safety.trusted_config()
    assert config['current-context'] == 'kind-cka-14d'
    assert config['clusters'][0]['cluster']['server'] == 'https://cka-14d-control-plane:6443'


def test_host_mode_uses_external_endpoint(monkeypatch):
    monkeypatch.delenv('CKA_CONTAINER')
    monkeypatch.setattr(safety, 'run', fake_runner())
    assert safety.trusted_config()['clusters'][0]['cluster']['server'].startswith('https://127.0.0.1')


@pytest.mark.parametrize('labels', [
    {'io.x-k8s.kind.cluster': 'production', 'io.x-k8s.kind.role': 'control-plane'},
    {'io.x-k8s.kind.cluster': 'cka-14d', 'io.x-k8s.kind.role': 'worker'},
    {},
])
def test_refuses_container_that_is_not_the_lab_control_plane(monkeypatch, labels):
    monkeypatch.setattr(safety, 'run', fake_runner(labels=labels))
    with pytest.raises(RuntimeError, match='REFUSED'):
        safety.trusted_config()


def test_refuses_when_context_missing(monkeypatch):
    active = kind_config()
    active['contexts'] = [{'name': 'prod-admin', 'context': {'cluster': 'kind-cka-14d', 'user': 'kind-cka-14d'}}]
    monkeypatch.setattr(safety, 'run', fake_runner(active=active))
    with pytest.raises(RuntimeError, match='context missing'):
        safety.trusted_config()


def test_refuses_context_name_hijacked_to_other_cluster(monkeypatch):
    """A context merely *named* kind-cka-14d that points at a different CA must be rejected."""
    monkeypatch.setattr(safety, 'run', fake_runner(active=kind_config(server='https://prod.example:6443', ca='UFJPRA==')))
    with pytest.raises(RuntimeError, match='CA does not match'):
        safety.trusted_config()


def test_snapshot_pins_day_namespace(monkeypatch):
    monkeypatch.setattr(safety, 'run', fake_runner())
    path = safety.snapshot(7)
    with open(path, encoding='utf-8') as stream:
        config = json.load(stream)
    assert config['contexts'][0]['context']['namespace'] == 'cka-d07'
    assert config['current-context'] == 'kind-cka-14d'


@pytest.mark.parametrize('day', [0, 21, -1])
def test_snapshot_rejects_out_of_range_day(monkeypatch, day):
    monkeypatch.setattr(safety, 'run', fake_runner())
    with pytest.raises(ValueError):
        safety.snapshot(day)
