#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 12
echo "Preparing Day 12..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: faulty-image
spec:
  replicas: 1
  selector:
    matchLabels:
      app: faulty-image
  template:
    metadata:
      labels:
        app: faulty-image
    spec:
      containers:
      - name: nginx
        image: nginx:bad-tag-cka
        ports:
        - containerPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: payments
  template:
    metadata:
      labels:
        app: payments
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
  name: payments-svc
spec:
  selector:
    app: incorrect-selector
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
  name: allowed-client
  labels:
    role: allowed
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 12 ready. Read: $ROOT/days/day12/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
