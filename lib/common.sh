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
  [[ "$1" =~ ^(0?[1-9]|1[0-9]|20)$ ]] || { echo 'Invalid day' >&2; return 2; }
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
# Run a command on a kind node container. Only the three nodes of the dedicated lab are accepted.
node_exec() {
  local node="$1"; shift
  case "$node" in cka-14d-control-plane|cka-14d-worker|cka-14d-worker2) ;; *) echo "REFUSED: $node is not a lab node" >&2; return 2 ;; esac
  require_cmd docker
  docker exec "$node" "$@"
}
METRICS_SERVER_VERSION=v0.9.1
ensure_metrics_server() {
  if kubectl -n kube-system get deployment metrics-server >/dev/null 2>&1; then return 0; fi
  echo "Installing metrics-server $METRICS_SERVER_VERSION (kind needs --kubelet-insecure-tls)..."
  kubectl apply -f "https://github.com/kubernetes-sigs/metrics-server/releases/download/$METRICS_SERVER_VERSION/components.yaml" >/dev/null
  kubectl -n kube-system patch deployment metrics-server --type=json \
    -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]' >/dev/null
  kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s
}
# Exam control planes have etcdctl on the node; copy it (and etcdutl) out of the running etcd container.
ensure_node_etcdctl() {
  node_exec cka-14d-control-plane sh -c '
    command -v etcdctl >/dev/null && command -v etcdutl >/dev/null && exit 0
    id=$(crictl ps --name "^etcd$" -q | head -1)
    pid=$(crictl inspect -o go-template --template "{{.info.pid}}" "$id")
    cp "/proc/$pid/root/usr/local/bin/etcdctl" "/proc/$pid/root/usr/local/bin/etcdutl" /usr/local/bin/'
}
# Cluster-scoped objects and node files a day may leave behind.
cleanup_cluster_scope() {
  case "$1" in
    04) kubectl delete pv cka-d04-local-pv --ignore-not-found --wait=false ;;
    06) kubectl delete clusterrole,clusterrolebinding cka-d06-node-reader --ignore-not-found ;;
    15) node_exec cka-14d-worker rm -f /etc/kubernetes/manifests/static-web.yaml
        node_exec cka-14d-control-plane rm -rf /opt/cka-etcd
        kubectl delete csr jane --ignore-not-found ;;
    16) kubectl delete priorityclass critical-batch --ignore-not-found ;;
    18) kubectl delete namespace cka-d18-frontend --ignore-not-found --wait=false ;;
    20) kubectl delete crd backups.cka.io --ignore-not-found ;;
  esac
}
cleanup_day() {
  require_lab_cluster
  local ns
  ns="$(ns_for_day "$1")"
  # Static Pods must go before their namespace, or the kubelet keeps recreating mirror Pods.
  cleanup_cluster_scope "$1"
  kubectl delete namespace "$ns" --ignore-not-found --wait=true --timeout=180s
  restore_day_nodes "$1"
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
