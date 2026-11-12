#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 07
echo "Preparing Day 07..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: broken-app
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "exit 1"]

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-image
spec:
  replicas: 1
  selector:
    matchLabels:
      app: broken-image
  template:
    metadata:
      labels:
        app: broken-image
    spec:
      containers:
      - name: nginx
        image: nginx:nonexistent-cka-tag
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Pod
metadata:
  name: pending-app
spec:
  containers:
  - name: app
    image: nginx:1.27
    resources:
      requests:
        cpu: "1000"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 1
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
    app: wrong-app
  ports:
  - port: 80
    targetPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-probe
spec:
  replicas: 2
  selector:
    matchLabels:
      app: broken-probe
  template:
    metadata:
      labels:
        app: broken-probe
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        readinessProbe:
          httpGet:
            path: /
            port: 9999
          initialDelaySeconds: 2
          periodSeconds: 5
MANIFEST
echo "Day 07 ready. Read: $ROOT/days/day07/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
