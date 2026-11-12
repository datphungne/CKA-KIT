#!/usr/bin/env bash
set -euo pipefail
# Terminal containers use the same image but never bootstrap or mount Docker.
if [[ "${CKA_CONTAINER:-}" == 1 ]]; then
  # Terminal shells orphaned by a previous console crash/restart (labelled by app.py).
  stale="$(docker ps -aq --filter label=cka-kit.terminal=1 2>/dev/null || true)"
  if [[ -n "$stale" ]]; then
    echo "Removing $(wc -w <<<"$stale") orphaned lab terminal container(s)"
    docker rm -f $stale >/dev/null || true
  fi
  python /workspace/lib/runtime.py
fi
exec "$@"
