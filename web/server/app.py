"""Local-only UI for real Kubernetes practice. No cloud backend, no fake API state.

All resource data is fetched from the learner's disposable kind cluster.
Shell access is an intentional local-only feature: never publish port 8765.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import struct
import subprocess
import sys
import threading
import time
import uuid
from typing import Literal
from concurrent.futures import ThreadPoolExecutor
import codecs

if os.name == "posix":
    import pty
    import fcntl
    import termios

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / 'web' / 'static'
CONTEXT = 'kind-cka-14d'
CLUSTER = 'cka-14d'
JOB_TTL = 3600
sys.path.insert(0, str(ROOT / 'lib'))
from safety import snapshot, trusted_config
from netguard import from_lab_network, lab_networks

MAX_TERMINALS = 4


def local_origin(headers):
    host = headers.get('host', '')
    return host in ('localhost:8765', '127.0.0.1:8765') and headers.get('origin') == f'http://{host}'


async def lab_client(client) -> bool:
    """True when the TCP peer sits on kind's network (a lab terminal or Pod), whatever its headers say."""
    networks = await asyncio.to_thread(lab_networks)
    return from_lab_network(client.host if client else None, networks)

app = FastAPI(title='CKA-KIT Local Lab', docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', '127.0.0.1:8765', 'localhost:8765'])
app.mount('/static', StaticFiles(directory=str(STATIC)), name='static')

_jobs: dict[str, dict] = {}
_job_lock = threading.Lock()
_busy = threading.Lock()
_terminals = set()


@app.middleware('http')
async def protect_local_api(request: Request, call_next):
    if await lab_client(request.client):
        return JSONResponse({'detail': 'Console is not reachable from lab workloads'}, status_code=403)
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and not local_origin(request.headers):
        return JSONResponse({'detail': 'Same-origin localhost request required'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws://127.0.0.1:8765 ws://localhost:8765; frame-ancestors 'none'"
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response



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
    try:
        trusted_config()
        return True
    except Exception:
        return False


def kubectl(*args: str, timeout=8) -> dict:
    return cli(['kubectl', '--context', CONTEXT, '--request-timeout=5s', *args], timeout=timeout)


def objects(*args: str) -> list:
    r = kubectl(*args, '-o', 'json')
    if not r['ok']:
        raise RuntimeError(r['stderr'] or 'Kubernetes request failed')
    return json.loads(r['stdout']).get('items', [])


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
    error = ''
    try:
        nodes = objects('get', 'nodes') if ready else []
    except (RuntimeError, ValueError) as exc:
        nodes = []
        ready = False
        error = str(exc)
    if exists and not ready and not error:
        error = api.get('stderr', 'Kubernetes API unavailable')

    return {'tools': tools, 'error': error, 'context': context, 'expectedContext': CONTEXT,
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
    ns = namespace(day)
    kinds = ['pods', 'deployments', 'services', 'events', 'nodes']
    try:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(objects, *(['-n', ns] if kind != 'nodes' else []), 'get', kind) for kind in kinds]
            pods, deployments, services, events, nodes = [f.result() for f in futures]
    except (RuntimeError, ValueError, TypeError) as exc:
        return {'connected': False, 'error': str(exc), **{kind: [] for kind in kinds}}
    events.sort(key=lambda e: e.get('lastTimestamp') or e.get('eventTime') or e.get('metadata', {}).get('creationTimestamp', ''))
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
                             text=True, bufsize=1, env=os.environ.copy(), start_new_session=True)
        with _job_lock:
            job['pid'] = p.pid
        assert p.stdout is not None
        def expire():
            job['output'] += '\nAction timed out after 15 minutes.\n'
            if p.poll() is None:
                if os.name == 'posix':
                    os.killpg(p.pid, signal.SIGKILL)
                else:
                    p.kill()
        deadline = threading.Timer(900, expire)
        deadline.daemon = True
        deadline.start()
        for line in p.stdout:
            with _job_lock:
                job['output'] = (job['output'] + line)[-160_000:]
        code = p.wait()
        deadline.cancel()
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
            raise HTTPException(412, 'Dedicated kind lab identity could not be verified; run Diagnose')
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
    return snapshot(safe_day(day))


def terminal_command(day, config, name):
    if os.environ.get('CKA_CONTAINER') != '1':
        raise RuntimeError('Start with docker compose up --build for the isolated terminal.')
    return ['docker', 'run', '--rm', '--init', '-it', '--name', name, '--label', 'cka-kit.terminal=1',
            '--network', 'kind', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--memory=512m', '--pids-limit=128',
            '-v', 'cka-kit-config:/lab:ro', '-v', 'cka-kit-answers:/workspace/answers',
            '-e', f'KUBECONFIG={config}', '-e', f'CKA_NS={namespace(day)}',
            '-e', 'TERM=xterm-256color', '-e', 'HISTFILE=/dev/null',
            '-e', f'CKA_DAY={day:02d}',
            'cka-kit:local', 'bash', '--noprofile', '--rcfile', '/workspace/web/terminal.bashrc', '-i']


def reap_terminal_container(name: str, attempts: int = 3, delay: float = 1.0) -> bool:
    """Force-remove a terminal container until Docker no longer lists it. Returns True once gone."""
    for _ in range(attempts):
        cli(['docker', 'rm', '-f', name], 10)
        listed = cli(['docker', 'ps', '-aq', '--filter', f'name=^/{name}$'], 10)
        if listed['ok'] and not listed['stdout'].strip():
            return True
        time.sleep(delay)
    return False


@app.websocket('/ws/terminal/{day}')
async def terminal(ws: WebSocket, day: int):
    # HTTP middleware does not run for WebSockets, so repeat the network check here.
    from_lab = await lab_client(ws.client)
    # No await between the capacity check and the reservation, so concurrent handshakes cannot exceed the cap.
    if from_lab or not 1 <= day <= 14 or not local_origin(ws.headers) or len(_terminals) >= MAX_TERMINALS:
        await ws.close(code=1008)
        return
    name = 'cka-terminal-' + uuid.uuid4().hex[:12]
    _terminals.add(name)
    master = slave = -1
    child = None
    config = None
    reader = receiver = None
    try:
        await ws.accept()
        config = await asyncio.to_thread(terminal_config, day)
        args = terminal_command(day, config, name)
        master, slave = pty.openpty()
        # Docker allocates the controlling terminal inside the isolated container.
        child = subprocess.Popen(args, stdin=slave, stdout=slave, stderr=slave,
                                 start_new_session=True, close_fds=True)
        os.close(slave)
        slave = -1
        os.set_blocking(master, False)
        await ws.send_text('\r\nStarting isolated lab shell…\r\n')

        async def read_pty():
            decoder = codecs.getincrementaldecoder('utf-8')('replace')
            while True:
                readable = await asyncio.to_thread(select.select, [master], [], [], 0.2)
                if not readable[0]:
                    if child.poll() is not None:
                        break
                    continue
                try:
                    data = os.read(master, 65536)
                except (OSError, BlockingIOError):
                    break
                if not data:
                    break
                await ws.send_text(decoder.decode(data))

        async def receive_input():
            while True:
                message = await ws.receive_text()
                if len(message) > 65536:
                    raise ValueError('Terminal frame too large')
                data = json.loads(message)
                if not isinstance(data, dict):
                    raise ValueError('Expected an object')
                if data.get('type') == 'input' and isinstance(data.get('data'), str):
                    remaining = data['data'].encode('utf-8')
                    while remaining:
                        try:
                            count = os.write(master, remaining)
                            remaining = remaining[count:]
                        except BlockingIOError:
                            await asyncio.sleep(0.01)
                elif data.get('type') == 'resize':
                    cols = max(20, min(int(data.get('cols', 110)), 300))
                    rows = max(5, min(int(data.get('rows', 28)), 100))
                    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGWINCH)

        reader = asyncio.create_task(read_pty())
        receiver = asyncio.create_task(receive_input())
        done, pending = await asyncio.wait([reader, receiver], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    except (WebSocketDisconnect, json.JSONDecodeError, ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        try:
            await ws.send_text(f'\r\n{exc}\r\n')
        except (RuntimeError, WebSocketDisconnect):
            pass
    finally:
        for task in (reader, receiver):
            if task:
                task.cancel()
        await asyncio.gather(*(t for t in (reader, receiver) if t), return_exceptions=True)
        # Remove the sibling container even when bash ignores HUP/TERM.
        await asyncio.to_thread(cli, ['docker', 'rm', '-f', name], 10)
        if child and child.poll() is None:
            child.kill()
        if child:
            await asyncio.to_thread(child.wait)
            # Killing the docker CLI mid-create does not stop the daemon from starting the container.
            await asyncio.to_thread(reap_terminal_container, name)
        for fd in (master, slave):
            if fd >= 0:
                os.close(fd)
        if config:
            Path(config).unlink(missing_ok=True)
        _terminals.discard(name)
        try:
            await ws.close()
        except (RuntimeError, WebSocketDisconnect):
            pass
