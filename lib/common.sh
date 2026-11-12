#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_CONTEXT="kind-cka-14d"
require_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }
require_lab_cluster() {
  require_cmd kubectl
  require_cmd python3
  CKA_SAFE_CONFIG="$(python3 "$LAB_ROOT/lib/safety.py")" || exit 2
  export KUBECONFIG="$CKA_SAFE_CONFIG"
  trap 'rm -f -- "$CKA_SAFE_CONFIG"' EXIT
  kubectl --request-timeout=10s cluster-info >/dev/null
}
kubectl() { command kubectl --context "$EXPECTED_CONTEXT" "$@"; }
ns_for_day() {
  [[ "$1" =~ ^(0?[1-9]|1[0-4])$ ]] || { echo 'Invalid day' >&2; return 2; }
  printf 'cka-d%02d' "$((10#$1))"
}
restore_day_nodes() {
  local day="$1" node
  for node in cka-14d-worker cka-14d-worker2; do
    kubectl uncordon "$node" >/dev/null
    if [[ "$day" == 02 ]]; then
      kubectl taint node "$node" dedicated=exam:NoSchedule- >/dev/null 2>&1 || true
      kubectl label node "$node" disk- >/dev/null 2>&1 || true
    fi
  done
}
cleanup_day() {
  require_lab_cluster
  local ns
  ns="$(ns_for_day "$1")"
  kubectl delete namespace "$ns" --ignore-not-found --wait=true --timeout=120s
  restore_day_nodes "$1"
  if [[ "$1" == 06 ]]; then
    kubectl delete clusterrole,clusterrolebinding cka-d06-node-reader --ignore-not-found
  fi
  echo "Deleted namespace $ns."
}
reset_day() {
  cleanup_day "$1"
  local ns
  ns="$(ns_for_day "$1")"
  kubectl create namespace "$ns"
  kubectl label namespace "$ns" app.kubernetes.io/part-of=cka-14day-practice --overwrite
  export NS="$ns"
  mkdir -p "$LAB_ROOT/answers"
  echo "Preparing namespace: $ns"
}
wait_rollout() { kubectl -n "$NS" rollout status "deployment/$1" --timeout=120s; }
