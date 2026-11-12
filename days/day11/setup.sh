#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 11
echo "Preparing Day 11..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: memory-hog
spec:
  containers:
  - name: hog
    image: python:3.12-alpine
    command: ["python3", "-c", "x=bytearray(256*1024*1024); print('allocated', len(x), flush=True); import time; time.sleep(3600)"]
    resources:
      limits:
        memory: 32Mi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: probe-failure
spec:
  replicas: 2
  selector:
    matchLabels:
      app: probe-failure
  template:
    metadata:
      labels:
        app: probe-failure
    spec:
      containers:
      - name: web
        image: nginx:1.27
        readinessProbe:
          httpGet:
            path: /
            port: 8088
          periodSeconds: 5

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8082

---
apiVersion: v1
kind: Pod
metadata:
  name: diagnostics-client
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 11 ready. Read: $ROOT/days/day11/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
