"""Every reference solution marked `automated: true` must make the grader PASS on a real cluster.

Opt-in (needs the running console and a Ready cluster, ~15 min):
    CKA_INTEGRATION=1 python -m pytest tests/test_solutions.py -v
    CKA_DAYS=3,7 ... to run a subset.
"""
import os
import re
import subprocess

import pytest

from hints import load_hints
from test_integration import run_action, call

pytestmark = pytest.mark.skipif(os.environ.get('CKA_INTEGRATION') != '1', reason='set CKA_INTEGRATION=1')

DAYS = [int(d) for d in os.environ.get('CKA_DAYS', ','.join(map(str, range(1, 21)))).split(',')]
CONSOLE = 'cka-kit-console-1'

# Same environment the browser terminal gets: day namespace as default, cwd /workspace.
PRELUDE = '''set -eo pipefail
export KUBECONFIG="$(python3 /workspace/lib/safety.py {day})"
trap 'rm -f -- "$KUBECONFIG"' EXIT
export CKA_NS=cka-d{day:02d}
cd /workspace
'''


def run_solution(day: int, exercise: str, script: str, wait: int) -> subprocess.CompletedProcess:
    body = PRELUDE.format(day=day) + (f'sleep {wait}\n' if wait else '') + f'echo "### {exercise}"\n' + script
    # Send bytes: text mode on Windows would turn \n into \r\n and break bash.
    done = subprocess.run(['docker', 'exec', '-i', CONSOLE, 'bash', '-s'], input=body.encode('utf-8'),
                          capture_output=True, timeout=900)
    return subprocess.CompletedProcess(done.args, done.returncode,
                                       done.stdout.decode('utf-8', 'replace'), done.stderr.decode('utf-8', 'replace'))


@pytest.fixture(scope='module', autouse=True)
def cluster_ready():
    if not call('/api/status')['ready']:
        pytest.skip('kind-cka-14d is not ready')


@pytest.mark.parametrize('day', DAYS)
def test_reference_solutions_pass_grader(day):
    hints = load_hints(day)
    automated = {k: v for k, v in hints.items() if v['automated']}
    if not automated:
        pytest.skip(f'day {day:02d} has no automated solutions')
    existing = subprocess.run(['docker', 'exec', CONSOLE, 'sh', '-c', f'ls /workspace/answers/day{day:02d}-* 2>/dev/null'],
                              capture_output=True, text=True).stdout.split()
    if existing:
        pytest.skip(f'refusing to overwrite your answer files: {existing}')
    setup = run_action('setup', day)
    assert setup['code'] == 0, setup['output'][-2000:]
    try:
        for exercise, item in sorted(automated.items()):
            raw = load_raw_wait(day, exercise)
            result = run_solution(day, exercise, item['solution'], raw)
            assert result.returncode == 0, f'{exercise} solution failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}'
        verify = run_action('verify', day)
        states = {f'{day:02d}.{n}': s for s, n in re.findall(rf'\[(PASS|FAIL|MANUAL)\]\s+{day:02d}\.(\d+)', verify['output'])}
        failed = [k for k in automated if states.get(k) != 'PASS']
        assert not failed, f'not PASS after solution: {failed}\n{verify["output"][-3000:]}'
    finally:
        cleanup = run_action('cleanup', day)
        subprocess.run(['docker', 'exec', CONSOLE, 'sh', '-c', f'rm -rf /workspace/answers/day{day:02d}-*'], check=False)
        assert cleanup['code'] == 0, cleanup['output'][-2000:]


def load_raw_wait(day: int, exercise: str) -> int:
    """Optional `test_wait_seconds`: time a learner would naturally spend before this step."""
    import yaml
    from hints import hints_path
    data = yaml.safe_load(hints_path(day).read_text(encoding='utf-8'))
    return int(data['exercises'][exercise].get('test_wait_seconds', 0))
