#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_CONTEXT="kind-cka-14d"
require_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }
require_lab_cluster() {
  require_cmd kubectl
  local current
  current="$(kubectl config current-context 2>/dev/null || true)"
  if [[ "$current" != "$EXPECTED_CONTEXT" ]]; then
    echo "REFUSED: current context is '${current:-none}', expected '$EXPECTED_CONTEXT'." >&2
    echo "Run: kubectl config use-context $EXPECTED_CONTEXT" >&2
    echo "This protects your workplace/production clusters." >&2
    exit 2
  fi
  kubectl --request-timeout=10s cluster-info >/dev/null
}
ns_for_day() { printf 'cka-d%02d' "$((10#$1))"; }
reset_day() {
  require_lab_cluster
  local ns="$(ns_for_day "$1")"
  echo "Resetting only namespace: $ns"
  kubectl delete namespace "$ns" --ignore-not-found --wait=true --timeout=120s
  kubectl create namespace "$ns"
  kubectl label namespace "$ns" app.kubernetes.io/part-of=cka-14day-practice --overwrite
  kubectl config set-context --current --namespace="$ns" >/dev/null
  export NS="$ns"
}
cleanup_day() {
  require_lab_cluster
  local ns="$(ns_for_day "$1")"
  kubectl delete namespace "$ns" --ignore-not-found --wait=true --timeout=120s
  echo "Deleted namespace $ns."
}
wait_rollout() { kubectl -n "$NS" rollout status "deployment/$1" --timeout=120s; }
