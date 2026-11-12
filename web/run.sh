#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if ! command -v python3 >/dev/null; then echo 'Install Python 3.10+ first.' >&2; exit 1; fi
if [[ ! -d .venv ]]; then
  echo 'Creating local Python virtual environment...'
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip -q install -r web/server/requirements.txt
printf '\nCKA-KIT local console: http://127.0.0.1:8765\n'
printf 'This server exposes an interactive LOCAL shell. Never make it public.\n\n'
exec python -m uvicorn --app-dir web/server app:app --host 127.0.0.1 --port 8765 --no-access-log
