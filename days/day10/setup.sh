#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 10
echo "Preparing Day 10..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
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
  name: backend-svc
spec:
  selector:
    app: missing-backend
  ports:
  - port: 80
    targetPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bad-image
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bad-image
  template:
    metadata:
      labels:
        app: bad-image
    spec:
      containers:
      - name: nginx
        image: nginx:invalid-cka-tag
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Pod
metadata:
  name: trusted-client
  labels:
    role: trusted
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]

---
apiVersion: v1
kind: Pod
metadata:
  name: untrusted-client
  labels:
    role: untrusted
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 10 ready. Read: $ROOT/days/day10/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
