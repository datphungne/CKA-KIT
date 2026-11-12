#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 19
echo "Preparing Day 19..."
ensure_metrics_server
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crashy
spec:
  replicas: 1
  selector:
    matchLabels: {app: crashy}
  template:
    metadata:
      labels: {app: crashy}
    spec:
      containers:
      - name: app
        image: busybox:1.36
        command: ["sh", "-c", "if [ -z \"$DB_HOST\" ]; then echo 'FATAL: DB_HOST is not set' >&2; exit 1; fi; echo \"connected to $DB_HOST\"; sleep 86400"]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-app
spec:
  replicas: 1
  selector:
    matchLabels: {app: config-app}
  template:
    metadata:
      labels: {app: config-app}
    spec:
      containers:
      - name: app
        image: busybox:1.36
        command: ["sh", "-c", "echo level=$LEVEL; sleep 86400"]
        envFrom:
        - configMapRef: {name: app-settings}
---
apiVersion: v1
kind: Pod
metadata:
  name: needs-storage
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
    volumeMounts:
    - {name: logs, mountPath: /logs}
  volumes:
  - name: logs
    persistentVolumeClaim: {claimName: logs-claim}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wrong-node
spec:
  replicas: 1
  selector:
    matchLabels: {app: wrong-node}
  template:
    metadata:
      labels: {app: wrong-node}
    spec:
      nodeSelector: {disktype: nvme}
      containers:
      - name: nginx
        image: nginx:1.27
---
apiVersion: v1
kind: Pod
metadata:
  name: cpu-burner
spec:
  containers:
  - name: burn
    image: busybox:1.36
    command: ["sh", "-c", "while true; do :; done"]
    resources:
      limits: {cpu: 300m}
---
apiVersion: v1
kind: Pod
metadata:
  name: idle-a
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
---
apiVersion: v1
kind: Pod
metadata:
  name: idle-b
spec:
  containers:
  - name: main
    image: nginx:1.27
MANIFEST
echo "Day 19 ready. Read: $ROOT/days/day19/TASKS.md"
