"""Refuse console traffic that originates on kind's Docker network.

The console joins the `kind` network to reach the API server, so lab terminal
containers and in-cluster Pods (NATed through node IPs) can open TCP connections
to it. Host/Origin headers are caller-controlled, so the decision is made on the
TCP source address instead: anything from a kind subnet is a lab workload, never
the learner's browser (which arrives through the published 127.0.0.1 port).
"""
from __future__ import annotations

import ipaddress
import json
import subprocess
import threading
import time

Network = ipaddress.IPv4Network | ipaddress.IPv6Network

TTL_SECONDS = 10
_lock = threading.Lock()
_cache: dict = {'at': float('-inf'), 'nets': ()}


def _inspect_kind_subnets() -> tuple[Network, ...]:
    out = subprocess.run(['docker', 'network', 'inspect', 'kind'], capture_output=True, text=True, timeout=5)
    if out.returncode != 0:
        return ()  # network absent: no terminal can exist, terminals require it
    config = json.loads(out.stdout)[0].get('IPAM', {}).get('Config') or []
    return tuple(ipaddress.ip_network(c['Subnet'], strict=False) for c in config if c.get('Subnet'))


def lab_networks() -> tuple[Network, ...]:
    """kind subnets, refreshed every few seconds; keeps the last known value if Docker hiccups."""
    with _lock:
        if time.monotonic() - _cache['at'] > TTL_SECONDS:
            try:
                _cache['nets'] = _inspect_kind_subnets()
            except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError):
                pass  # fail closed: keep previously known subnets
            _cache['at'] = time.monotonic()
        return _cache['nets']


def from_lab_network(client_ip: str | None, networks: tuple[Network, ...]) -> bool:
    """True if the address belongs to a lab network. Unparseable addresses are refused too."""
    if not client_ip:
        return True
    try:
        ip = ipaddress.ip_address(client_ip.split('%')[0])
    except ValueError:
        return True
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return any(ip.version == net.version and ip in net for net in networks)
