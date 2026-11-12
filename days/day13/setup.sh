#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 13
echo "Preparing Day 13..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-rollout
spec:
  replicas: 1
  selector:
    matchLabels:
      app: broken-rollout
  template:
    metadata:
      labels:
        app: broken-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:invalid-cka-tag
        ports:
        - containerPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
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
  name: gateway-svc
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
  name: tester
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 13 ready. Read: $ROOT/days/day13/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
