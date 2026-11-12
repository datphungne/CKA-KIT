#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 06
echo "Preparing Day 06..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintenance-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maintenance-app
  template:
    metadata:
      labels:
        app: maintenance-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Pod
metadata:
  name: rbac-client
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 06 ready. Read: $ROOT/days/day06/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
