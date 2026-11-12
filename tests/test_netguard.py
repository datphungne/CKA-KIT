"""lib/netguard.py decides on the TCP peer address, never on headers."""
import ipaddress
import json
import subprocess

import pytest

import netguard

NETS = (ipaddress.ip_network('172.19.0.0/16'), ipaddress.ip_network('fc00:f853:ccd:e793::/64'))


@pytest.mark.parametrize('ip', ['172.19.0.5', '172.19.255.1', 'fc00:f853:ccd:e793::5', '::ffff:172.19.0.9'])
def test_kind_addresses_are_lab(ip):
    assert netguard.from_lab_network(ip, NETS)


@pytest.mark.parametrize('ip', ['172.20.0.1', '127.0.0.1', '192.168.65.1', '::1'])
def test_browser_paths_are_not_lab(ip):
    assert not netguard.from_lab_network(ip, NETS)


@pytest.mark.parametrize('ip', [None, '', 'testclient', 'not-an-ip'])
def test_unknown_peers_are_refused(ip):
    assert netguard.from_lab_network(ip, NETS)


def test_reads_subnets_from_docker(monkeypatch):
    payload = json.dumps([{'IPAM': {'Config': [{'Subnet': '172.19.0.0/16'}, {'Subnet': 'fc00:f853:ccd:e793::/64'}]}}])
    monkeypatch.setattr(netguard.subprocess, 'run',
                        lambda *a, **k: subprocess.CompletedProcess(a, 0, payload, ''))
    monkeypatch.setitem(netguard._cache, 'at', float('-inf'))
    assert netguard.lab_networks() == NETS


def test_keeps_last_known_subnets_when_docker_fails(monkeypatch):
    monkeypatch.setitem(netguard._cache, 'nets', NETS)
    monkeypatch.setitem(netguard._cache, 'at', float('-inf'))

    def boom(*a, **k):
        raise subprocess.TimeoutExpired('docker', 5)
    monkeypatch.setattr(netguard.subprocess, 'run', boom)
    assert netguard.lab_networks() == NETS
