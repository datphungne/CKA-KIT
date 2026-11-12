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
# Pin image and release to stay aligned with CKA v1.37 as of Nov 2026.
IMAGE='kindest/node:v1.37.0@sha256:a1ed56cfb0e7b93589bdf97c8cd566405a265939e3620fc4f5de89adff580ae5'
kind create cluster --name cka-14d --image "$IMAGE" --config "$ROOT/cluster/kind-config.yaml"
kubectl config use-context kind-cka-14d
BASE='https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests'
echo 'Installing Calico CNI (network policy capable) on the disposable cluster...'
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
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
