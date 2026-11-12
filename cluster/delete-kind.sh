#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "--confirm-delete" ]]; then
  echo 'This PERMANENTLY deletes kind cluster cka-14d and all lab data.'
  echo 'Run: bash cluster/delete-kind.sh --confirm-delete'
  exit 2
fi
command -v kind >/dev/null || exit 1
kind delete cluster --name cka-14d
