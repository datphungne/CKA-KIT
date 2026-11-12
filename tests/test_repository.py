"""Static checks: lab content, shell scripts, grader coverage and packaging."""
import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
DAYS = [ROOT / 'days' / f'day{d:02d}' for d in range(1, 15)]
SCRIPTS = sorted(p for p in ROOT.rglob('*.sh') if '.git' not in p.parts)
BASH = shutil.which('bash')


@pytest.mark.parametrize('day', DAYS, ids=lambda p: p.name)
def test_day_folder_complete(day):
    for name in ('TASKS.md', 'setup.sh', 'verify.sh', 'cleanup.sh'):
        assert (day / name).is_file(), f'{day.name}/{name} missing'
    assert len(re.findall(r'^## Exercise \d{2}\.\d+ ', (day / 'TASKS.md').read_text(encoding='utf-8'), re.M)) == 5


def test_grader_has_five_checks_per_day():
    tree = ast.parse((ROOT / 'bin' / 'grade.py').read_text(encoding='utf-8'))
    tasks = next(n.value for n in ast.walk(tree)
                 if isinstance(n, ast.AnnAssign) and getattr(n.target, 'id', '') == 'TASKS')
    counts = {k.value: len(v.elts) for k, v in zip(tasks.keys, tasks.values, strict=True)}
    assert counts == {d: 5 for d in range(1, 15)}


@pytest.mark.skipif(not BASH, reason='bash not installed')
@pytest.mark.parametrize('script', SCRIPTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_shell_syntax(script):
    text = script.read_text(encoding='utf-8').replace('\r\n', '\n')
    result = subprocess.run([BASH, '-n'], input=text, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('day', DAYS, ids=lambda p: p.name)
def test_day_scripts_go_through_safety_guard(day):
    """Every script that touches the cluster must source common.sh and use its guarded helpers."""
    setup = (day / 'setup.sh').read_text(encoding='utf-8')
    verify = (day / 'verify.sh').read_text(encoding='utf-8')
    cleanup = (day / 'cleanup.sh').read_text(encoding='utf-8')
    for text in (setup, verify, cleanup):
        assert 'source "$ROOT/lib/common.sh"' in text
    assert 'reset_day' in setup
    assert 'require_lab_cluster' in verify
    assert 'cleanup_day' in cleanup
    assert 'config use-context' not in setup + cleanup


@pytest.mark.skipif(not BASH, reason='bash not installed')
@pytest.mark.parametrize('value,expected', [('1', 'cka-d01'), ('07', 'cka-d07'), ('14', 'cka-d14')])
def test_ns_for_day_valid(value, expected):
    out = subprocess.run([BASH, '-c', f'source lib/common.sh; ns_for_day "{value}"'],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout == expected


@pytest.mark.skipif(not BASH, reason='bash not installed')
@pytest.mark.parametrize('value', ['0', '15', 'abc', '1; rm -rf /', '', 'kube-system'])
def test_ns_for_day_rejects_everything_else(value):
    out = subprocess.run([BASH, '-c', 'source lib/common.sh; ns_for_day "$1"', '_', value],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode != 0
    assert 'kube-system' not in out.stdout


def test_compose_binds_loopback_and_hides_host_kubeconfig():
    compose = yaml.safe_load((ROOT / 'compose.yaml').read_text(encoding='utf-8'))
    console = compose['services']['console']
    assert all(str(p).startswith('127.0.0.1:') for p in console['ports'])
    mounts = ' '.join(console['volumes'])
    assert '.kube' not in mounts and '~' not in mounts and '$HOME' not in mounts


def test_ui_has_no_external_runtime_dependencies():
    html = (ROOT / 'web' / 'static' / 'index.html').read_text(encoding='utf-8')
    assert not re.search(r'(src|href)="https?://', html)
    for asset in re.findall(r'(?:src|href)="/static/([^"]+)"', html):
        assert (ROOT / 'web' / 'static' / asset).is_file(), asset


@pytest.mark.parametrize('path', ['web/static/app.js', 'web/static/index.html', 'web/server/app.py'])
def test_no_encoding_damage(path):
    """A cp1252 round-trip once turned '…', '·', '→' and '✓' into '?'. Keep it from coming back."""
    text = (ROOT / path).read_text(encoding='utf-8')
    assert '�' not in text
    damaged = ['exercises?', 'Running?', 'Preparing?', 'retrying?', 'workspace?', 'lab shell?',
               "'? Completed", ' ? Start the lab', ' ? real kubectl', ' ? 2 workers', 'kind-cka-14d ? ']
    assert [d for d in damaged if d in text] == []
