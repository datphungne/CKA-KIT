"""HINTS.yaml coverage and validity. Link liveness is opt-in: CKA_LINKCHECK=1."""
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from hints import EXAM_DOC_HOSTS, HintError, _check_exercise, load_hints

ROOT = Path(__file__).resolve().parents[1]
DAYS = range(1, 15)


def task_ids(day):
    text = (ROOT / 'days' / f'day{day:02d}' / 'TASKS.md').read_text(encoding='utf-8')
    return re.findall(r'^## Exercise (\d{2}\.\d) ', text, re.M)


@pytest.mark.parametrize('day', DAYS)
def test_every_exercise_has_hint_and_solution(day):
    hints = load_hints(day)
    assert sorted(hints) == sorted(task_ids(day))
    for key, item in hints.items():
        assert item['docs'], key
        assert len(item['hint']) > 40, f'{key}: hint too thin'
        assert len(item['solution'].strip().splitlines()) >= 2, f'{key}: solution too thin'


def test_at_least_most_solutions_are_machine_verified():
    automated = sum(v['automated'] for d in DAYS for v in load_hints(d).values())
    assert automated == 61, automated


@pytest.mark.parametrize('day', DAYS)
def test_solutions_do_not_touch_host_kubeconfig(day):
    for key, item in load_hints(day).items():
        assert '~/.kube/config' not in item['solution'], key
        assert 'config use-context' not in item['solution'], key


@pytest.mark.parametrize('url', [
    'http://kubernetes.io/docs/',           # not https
    'https://evil.example/kubernetes.io',    # wrong host
    'https://kubernetes.io.evil.example/',   # suffix trick
    'javascript:alert(1)',
])
def test_rejects_non_exam_links(url):
    with pytest.raises(HintError):
        _check_exercise('01.1', {'docs': [{'title': 'x', 'url': url}], 'hint': 'h', 'solution': 's'})


def test_day_api_serves_hints():
    from fastapi.testclient import TestClient
    import app as console
    client = TestClient(console.app, base_url='http://127.0.0.1:8765', client=('172.20.0.1', 1))
    body = client.get('/api/day/4').json()
    assert body['hintError'] == ''
    assert set(body['hints']) == {'04.1', '04.2', '04.3', '04.4', '04.5'}
    assert body['hints']['04.5']['docs'][0]['url'].startswith('https://kubernetes.io/')


def all_urls():
    return sorted({d['url'].split('#')[0] for day in DAYS for v in load_hints(day).values() for d in v['docs']})


@pytest.mark.skipif(os.environ.get('CKA_LINKCHECK') != '1', reason='set CKA_LINKCHECK=1 (needs internet)')
@pytest.mark.parametrize('url', all_urls())
def test_doc_links_resolve(url):
    assert any(url.startswith(f'https://{h}/') for h in EXAM_DOC_HOSTS)
    req = urllib.request.Request(url, headers={'User-Agent': 'cka-kit-linkcheck'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            assert resp.status == 200
            assert resp.geturl().rstrip('/') == url.rstrip('/') or 'kubernetes.io' in resp.geturl()
    except urllib.error.HTTPError as exc:
        pytest.fail(f'{url} -> HTTP {exc.code}')
