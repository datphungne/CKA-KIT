#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 02
echo "Preparing Day 02..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: store
spec:
  replicas: 4
  selector:
    matchLabels:
      app: store
  template:
    metadata:
      labels:
        app: store
    spec:
      containers:
      - name: nginx
        image: nginx:1.26
        ports:
        - containerPort: 80
MANIFEST
echo "Day 02 ready. Read: $ROOT/days/day02/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
