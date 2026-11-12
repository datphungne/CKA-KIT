#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 16
echo "Preparing Day 16..."
ensure_metrics_server
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels: {app: web}
  template:
    metadata:
      labels: {app: web}
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        resources:
          requests: {cpu: 50m, memory: 32Mi}
          limits: {cpu: 100m, memory: 64Mi}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hpa-app
spec:
  replicas: 1
  selector:
    matchLabels: {app: hpa-app}
  template:
    metadata:
      labels: {app: hpa-app}
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        resources:
          requests: {cpu: 100m, memory: 32Mi}
          limits: {cpu: 200m, memory: 64Mi}
MANIFEST
echo "Day 16 ready. Read: $ROOT/days/day16/TASKS.md"
