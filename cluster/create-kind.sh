#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for cmd in kind kubectl docker curl; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }; done
docker info >/dev/null 2>&1 || { echo 'Docker daemon is not running'; exit 1; }
if kind get clusters | grep -Fxq cka-14d; then
  echo 'Cluster cka-14d already exists. Refusing to overwrite it.'
  echo 'If intentional: kind delete cluster --name cka-14d'
  exit 1
fi
# Default node image from the kind v0.33.0 release notes (CKA curriculum v1.37).
# Calico v3.33 needs admissionregistration.k8s.io/v1 MutatingAdmissionPolicy, i.e. Kubernetes >= 1.36.
IMAGE='kindest/node:v1.37.0@sha256:a1ed56cfb0e7b93589bdf97c8cd566405a265939e3620fc4f5de89adff580ae5'
export KUBECONFIG="${KUBECONFIG:-$ROOT/.runtime/config}"
mkdir -p "$(dirname "$KUBECONFIG")"
# If anything below fails, remove the half-built cluster this run created so "Create" can simply be retried.
created=0
rollback() {
  local code=$?
  if [[ $code -ne 0 && $created -eq 1 ]]; then
    echo "Cluster setup failed (exit $code). Removing the partially created cka-14d cluster so you can retry..." >&2
    kind delete cluster --name cka-14d >&2 || true
  fi
}
trap rollback EXIT
kind create cluster --name cka-14d --image "$IMAGE" --config "$ROOT/cluster/kind-config.yaml"
created=1
if [[ "${CKA_CONTAINER:-}" == 1 ]]; then
  python3 "$ROOT/lib/runtime.py"
fi
chmod 600 "$KUBECONFIG"
source "$ROOT/lib/common.sh"
require_lab_cluster
BASE='https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests'
echo 'Installing Calico CNI (network policy capable) on the disposable cluster...'
TMP="$(mktemp -d)"
# require_lab_cluster and mktemp both need cleanup; keep the rollback first so it sees the real exit code.
trap 'rollback; rm -rf "$TMP"; rm -f -- "${CKA_SAFE_CONFIG:-}"' EXIT
curl -fsSL "$BASE/v3_projectcalico_org.yaml" -o "$TMP/calico-crds.yaml"
curl -fsSL "$BASE/tigera-operator.yaml" -o "$TMP/tigera-operator.yaml"
curl -fsSL "$BASE/custom-resources.yaml" -o "$TMP/custom-resources.yaml"
kubectl create -f "$TMP/calico-crds.yaml"
kubectl create -f "$TMP/tigera-operator.yaml"
kubectl wait --for=condition=Established crd/installations.operator.tigera.io --timeout=120s
kubectl create -f "$TMP/custom-resources.yaml"
echo 'Waiting for Calico workloads and Ready nodes...'
kubectl wait --for=condition=Ready nodes --all --timeout=420s
kubectl get nodes -o wide
kubectl get pods -n calico-system 2>/dev/null || true
kubectl get storageclass
cat <<'MSG'

Cluster is ready! Start with:
  bash days/day01/setup.sh
  cat days/day01/TASKS.md
  bash days/day01/verify.sh

Note: Ingress/Gateway controller and metrics-server are NOT installed by default.
An Ingress/Gateway object alone does not route traffic.
MSG
