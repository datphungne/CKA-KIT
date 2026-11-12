#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 18
echo "Preparing Day 18..."
kubectl wait --for=delete namespace/cka-d18-frontend --timeout=120s 2>/dev/null || true
kubectl create namespace cka-d18-frontend
kubectl label namespace cka-d18-frontend team=frontend app.kubernetes.io/part-of=cka-14day-practice
kubectl -n cka-d18-frontend run fe-client --image=busybox:1.36 --command -- sh -c 'sleep 86400'
kubectl -n "$NS" create deployment web --image=nginx:1.27
kubectl -n "$NS" create deployment api --image=nginx:1.27
kubectl -n "$NS" expose deployment web --port=80
kubectl -n "$NS" expose deployment api --port=80
kubectl -n "$NS" run client --image=busybox:1.36 --labels=role=client --command -- sh -c 'sleep 86400'
kubectl -n "$NS" run other-client --image=busybox:1.36 --labels=role=other --command -- sh -c 'sleep 86400'
kubectl -n "$NS" rollout status deployment/web --timeout=120s
kubectl -n "$NS" rollout status deployment/api --timeout=120s
echo "Day 18 ready. Read: $ROOT/days/day18/TASKS.md"
