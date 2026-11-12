#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
cleanup_day 04
kubectl delete pv cka-d04-local-pv --ignore-not-found --wait=false >/dev/null || true
kubectl delete storageclass cka-d04-manual --ignore-not-found >/dev/null || true
