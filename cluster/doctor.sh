#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/lib/common.sh"
for cmd in kind docker python3; do
  if command -v "$cmd" >/dev/null; then echo "OK $cmd"; else echo "MISSING $cmd"; fi
done
docker info >/dev/null 2>&1 || { echo "Docker daemon is not running"; exit 1; }
require_lab_cluster
kubectl get nodes -o wide
kubectl get storageclass
kubectl -n calico-system get daemonset 2>/dev/null || echo 'Calico daemonset not found'
if kubectl api-resources | grep -q '^gateways '; then echo 'Gateway API CRDs: installed'; else echo 'Gateway API CRDs: not installed'; fi
if kubectl -n kube-system get deployment metrics-server >/dev/null 2>&1; then echo 'metrics-server: installed'; else echo 'metrics-server: not installed'; fi
