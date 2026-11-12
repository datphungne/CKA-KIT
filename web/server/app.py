"""Local-only UI for real Kubernetes practice. No cloud backend, no fake API state.

All resource data is fetched from the learner's disposable kind cluster.
Shell access is an intentional local-only feature: never publish port 8765.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import fcntl
import termios
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / 'web' / 'static'
CONTEXT = 'kind-cka-14d'
CLUSTER = 'cka-14d'
JOB_TTL = 3600
app = FastAPI(title='CKA-KIT Local Lab', docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', '127.0.0.1:8765', 'localhost:8765'])
app.mount('/static', StaticFiles(directory=str(STATIC)), name='static')

_jobs: dict[str, dict] = {}
_job_lock = threading.Lock()
_busy = threading.Lock()


def cli(args: list[str], timeout=9, env=None) -> dict:
    try:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=ROOT, timeout=timeout, env=env)
        return {'ok': result.returncode == 0, 'code': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'ok': False, 'code': -1, 'stdout': '', 'stderr': str(exc)}


def safe_day(day: int) -> int:
    if not 1 <= day <= 14:
        raise HTTPException(400, 'Day must be between 1 and 14')
    return day


def namespace(day: int) -> str:
    return f'cka-d{day:02d}'


def expected_context() -> bool:
    r = cli(['kubectl', 'config', 'current-context'])
    return r['ok'] and r['stdout'].strip() == CONTEXT


def kubectl(*args: str, timeout=8) -> dict:
    # Explicit --context even if the active context is changed elsewhere.
    return cli(['kubectl', '--context', CONTEXT, '--request-timeout=5s', *args], timeout=timeout)


def objects(*args: str) -> list:
    r = kubectl(*args, '-o', 'json')
    if not r['ok']:
        return []
    try:
        return json.loads(r['stdout']).get('items', [])
    except (json.JSONDecodeError, TypeError):
        return []


def pod_status(o):
    state = o.get('status', {})
    waiting = next((s.get('state', {}).get('waiting', {}).get('reason') for s in state.get('containerStatuses', [])
                    if s.get('state', {}).get('waiting')), None)
    return waiting or state.get('phase', 'Unknown')


def iso_day(day: int):
    safe_day(day)
    path = ROOT / 'days' / f'day{day:02d}' / 'TASKS.md'
    return path.read_text(encoding='utf-8')


@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html', headers={'Cache-Control': 'no-store'})


@app.get('/api/status')
def status():
    tools = {name: shutil.which(name) is not None for name in ('kubectl', 'kind', 'docker', 'bash', 'python3')}
    context = cli(['kubectl', 'config', 'current-context'])['stdout'].strip() if tools['kubectl'] else ''
    clusters = cli(['kind', 'get', 'clusters'], timeout=8) if tools['kind'] else {'stdout': ''}
    exists = CLUSTER in clusters['stdout'].splitlines()
    api = kubectl('get', '--raw=/readyz') if exists and tools['kubectl'] else {'ok': False}
    ready = bool(api['ok'])
    nodes = objects('get', 'nodes') if ready else []
    return {'tools': tools, 'context': context, 'expectedContext': CONTEXT,
            'clusterExists': exists, 'ready': ready, 'nodes': len(nodes),
            'readyNodes': sum(1 for n in nodes if any(c.get('type') == 'Ready' and c.get('status') == 'True'
                                             for c in n.get('status', {}).get('conditions', []))),
            'activeJob': next((j['id'] for j in list(_jobs.values())[::-1] if j['state'] == 'running'), None)}


@app.get('/api/day/{day}')
def get_day(day: int):
    return {'day': safe_day(day), 'namespace': namespace(day), 'markdown': iso_day(day)}


@app.get('/api/resources/{day}')
def resources(day: int):
    safe_day(day)
    if not kubectl('get', '--raw=/readyz')['ok']:
        return {'connected': False, 'pods': [], 'deployments': [], 'services': [], 'events': [], 'nodes': []}
    ns = namespace(day)
    pods = objects('-n', ns, 'get', 'pods')
    deployments = objects('-n', ns, 'get', 'deployments')
    services = objects('-n', ns, 'get', 'services')
    events = objects('-n', ns, 'get', 'events')
    nodes = objects('get', 'nodes')
    return {
        'connected': True,
        'pods': [{'name': p['metadata']['name'], 'status': pod_status(p),
                  'ready': f"{sum(1 for s in p.get('status', {}).get('containerStatuses', []) if s.get('ready'))}/{len(p.get('spec', {}).get('containers', []))}",
                  'node': p.get('spec', {}).get('nodeName', '—'),
                  'restarts': sum(s.get('restartCount', 0) for s in p.get('status', {}).get('containerStatuses', [])),
                  'age': p['metadata'].get('creationTimestamp', '')} for p in pods],
        'deployments': [{'name': d['metadata']['name'], 'ready': f"{d.get('status', {}).get('readyReplicas', 0)}/{d.get('spec', {}).get('replicas', 1)}",
                         'image': ', '.join(c.get('image', '') for c in d.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])),
                         'age': d['metadata'].get('creationTimestamp', '')} for d in deployments],
        'services': [{'name': s['metadata']['name'], 'type': s.get('spec', {}).get('type', ''),
                      'clusterIP': s.get('spec', {}).get('clusterIP', ''),
                      'ports': ', '.join(str(p.get('port')) + ('→' + str(p.get('targetPort')) if p.get('targetPort') else '') for p in s.get('spec', {}).get('ports', []))} for s in services],
        'events': [{'reason': e.get('reason', ''), 'message': e.get('message', ''),
                    'kind': e.get('involvedObject', {}).get('kind', ''),
                    'name': e.get('involvedObject', {}).get('name', ''),
                    'type': e.get('type', ''), 'time': e.get('lastTimestamp', '') or e.get('eventTime', '')} for e in events][-40:][::-1],
        'nodes': [{'name': n['metadata']['name'],
                   'ready': any(c.get('type') == 'Ready' and c.get('status') == 'True' for c in n.get('status', {}).get('conditions', [])),
                   'version': n.get('status', {}).get('nodeInfo', {}).get('kubeletVersion', ''),
                   'roles': ', '.join(k.split('/')[-1] for k in n['metadata'].get('labels', {}) if k.startswith('node-role.kubernetes.io/')) or 'worker'} for n in nodes]
    }


class Action(BaseModel):
    action: Literal['create-cluster', 'doctor', 'setup', 'verify', 'cleanup']
    day: int = Field(default=1, ge=1, le=14)


def command_for(req: Action) -> list[str]:
    scripts = {
        'create-cluster': [str(ROOT / 'cluster/create-kind.sh')],
        'doctor': [str(ROOT / 'cluster/doctor.sh')],
        'setup': [str(ROOT / f'days/day{req.day:02d}/setup.sh')],
        'verify': [str(ROOT / f'days/day{req.day:02d}/verify.sh')],
        'cleanup': [str(ROOT / f'days/day{req.day:02d}/cleanup.sh')],
    }
    return ['bash', *scripts[req.action]]


def launch_job(job: dict, args: list[str]):
    try:
        p = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1, env=os.environ.copy())
        with _job_lock:
            job['pid'] = p.pid
        assert p.stdout is not None
        for line in p.stdout:
            with _job_lock:
                job['output'] = (job['output'] + line)[-160_000:]
        code = p.wait()
        with _job_lock:
            job['code'] = code
            job['state'] = 'finished'
            job['ended'] = time.time()
    except Exception as exc:
        with _job_lock:
            job['output'] += f'\nERROR: {exc}\n'
            job['code'] = -1
            job['state'] = 'finished'
            job['ended'] = time.time()
    finally:
        _busy.release()


@app.post('/api/action')
def action(req: Action):
    if not _busy.acquire(blocking=False):
        raise HTTPException(409, 'Another lab action is already running')
    try:
        if req.action not in ('create-cluster', 'doctor') and not expected_context():
            raise HTTPException(412, f'Current kubectl context must be {CONTEXT}; refusing to touch any other cluster')
        if req.action == 'create-cluster' and cli(['kind', 'get', 'clusters'])['stdout'].splitlines().count(CLUSTER):
            raise HTTPException(409, 'Disposable cluster already exists')
        now = time.time()
        with _job_lock:
            for key in list(_jobs):
                if _jobs[key].get('ended', now) < now - JOB_TTL:
                    del _jobs[key]
            id_ = uuid.uuid4().hex[:12]
            job = {'id': id_, 'action': req.action, 'day': req.day, 'state': 'running',
                   'started': now, 'output': f'$ {" ".join(command_for(req))}\n', 'code': None, 'pid': None}
            _jobs[id_] = job
        threading.Thread(target=launch_job, args=(job, command_for(req)), daemon=True).start()
        return {'id': id_}
    except Exception:
        _busy.release()
        raise


@app.get('/api/job/{job_id}')
def job(job_id: str):
    if not re.fullmatch('[a-f0-9]{12}', job_id) or job_id not in _jobs:
        raise HTTPException(404, 'Unknown job')
    with _job_lock:
        return dict(_jobs[job_id])


@app.get('/api/health')
def health():
    return {'ok': True, 'mode': 'LOCAL_REAL_KUBERNETES'}


def terminal_config(day: int) -> str:
    """Generate a context-minified config so ordinary shell kubectl stays on the lab cluster."""
    out = cli(['kubectl', 'config', 'view', '--raw', '--flatten', '--minify', '--context', CONTEXT], timeout=10)
    if not out['ok'] or not out['stdout'].strip():
        raise RuntimeError('Cluster config not found. Create kind-cka-14d first.')
    # Only this single cluster/user/context is present; no production contexts.
    tmp_dir = Path(tempfile.mkdtemp(prefix='cka-ui-kubeconfig-'))
    path = tmp_dir / 'config'
    path.write_text(out['stdout'], encoding='utf-8')
    path.chmod(0o600)
    cli(['kubectl', '--kubeconfig', str(path), 'config', 'set-context', '--current', '--namespace', namespace(day)])
    return str(path)


@app.websocket('/ws/terminal/{day}')
async def terminal(ws: WebSocket, day: int):
    if not 1 <= day <= 14:
        await ws.close(code=1008)
        return
    origin = ws.headers.get('origin', '')
    host = ws.headers.get('host', '')
    if host not in ('localhost:8765', '127.0.0.1:8765') or (origin and origin not in ('http://localhost:8765', 'http://127.0.0.1:8765')):
        await ws.close(code=1008)
        return
    await ws.accept()
    if os.name != 'posix' or not shutil.which('bash'):
        await ws.send_text('\r\nReal terminal requires Linux / macOS / WSL2 bash.\r\n')
        await ws.close()
        return
    try:
        config = terminal_config(day)
    except RuntimeError as exc:
        await ws.send_text('\r\n' + str(exc) + '\r\n')
        await ws.close()
        return
    master = slave = -1
    child = None
    try:
        master, slave = pty.openpty()
        env = os.environ.copy()
        env.update({'KUBECONFIG': config, 'CKA_NS': namespace(day), 'TERM': 'xterm-256color',
                    'PS1': fr'\[\033[1;34m\]cka:{day:02d}\[\033[0m\] \w $ ',
                    'HISTFILE': '/dev/null'})
        def configure_pty():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

        child = subprocess.Popen(['bash', '--noprofile', '--norc', '-i'], stdin=slave, stdout=slave, stderr=slave,
                                 cwd=ROOT, env=env, preexec_fn=configure_pty, close_fds=True)
        os.close(slave)
        slave = -1
        os.write(master, b'alias k=kubectl\nclear\nprintf "CKA terminal (real Kubernetes) | namespace: $CKA_NS\\n"\n')

        async def read_pty():
            while child and child.poll() is None:
                readable = await asyncio.to_thread(select.select, [master], [], [], 0.25)
                if not readable[0]:
                    continue
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                await ws.send_text(data.decode('utf-8', errors='replace'))

        reader = asyncio.create_task(read_pty())
        try:
            while True:
                msg = await ws.receive_text()
                data = json.loads(msg)
                if data.get('type') == 'input' and isinstance(data.get('data'), str):
                    os.write(master, data['data'][:8192].encode('utf-8'))
                elif data.get('type') == 'resize':
                    cols = max(20, min(int(data.get('cols', 110)), 300))
                    rows = max(10, min(int(data.get('rows', 28)), 100))
                    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
                    try:
                        os.killpg(child.pid, signal.SIGWINCH)
                    except ProcessLookupError:
                        pass
        except (WebSocketDisconnect, json.JSONDecodeError, OSError):
            pass
        finally:
            reader.cancel()
            try:
                await reader
            except (asyncio.CancelledError, OSError):
                pass
    finally:
        if child and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for fd in (master, slave):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        shutil.rmtree(Path(config).parent, ignore_errors=True)
