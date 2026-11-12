#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 08
echo "Preparing Day 08..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: upstream
spec:
  replicas: 1
  selector:
    matchLabels:
      app: upstream
  template:
    metadata:
      labels:
        app: upstream
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
  name: upstream-svc
spec:
  selector:
    app: upstream
  ports:
  - port: 80
    targetPort: 8081

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dns-backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dns-backend
  template:
    metadata:
      labels:
        app: dns-backend
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
  name: dns-backend-svc
spec:
  selector:
    app: dns-backend
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
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduling-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: scheduling-app
  template:
    metadata:
      labels:
        app: scheduling-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        ports:
        - containerPort: 80
MANIFEST
echo "Day 08 ready. Read: $ROOT/days/day08/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
