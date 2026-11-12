#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "--confirm-delete" ]]; then
  echo 'This PERMANENTLY deletes kind cluster cka-14d and all lab data.'
  echo 'Run: bash cluster/delete-kind.sh --confirm-delete'
  exit 2
fi
command -v kind >/dev/null || exit 1
# Check node identity even if the Kubernetes API is down.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
config="$(python3 "$ROOT/lib/safety.py")" || exit 2
trap 'rm -f -- "$config"' EXIT
kind delete cluster --name cka-14d
