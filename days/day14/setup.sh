#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 14
echo "Preparing Day 14..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: billing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: billing
  template:
    metadata:
      labels:
        app: billing
    spec:
      containers:
      - name: nginx
        image: nginx:does-not-exist
        ports:
        - containerPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 1
  selector:
    matchLabels:
      app: orders
  template:
    metadata:
      labels:
        app: orders
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
  name: orders-svc
spec:
  selector:
    app: wrong
  ports:
  - port: 80
    targetPort: 80

---
apiVersion: v1
kind: Pod
metadata:
  name: net-client
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]

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
echo "Day 14 ready. Read: $ROOT/days/day14/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
