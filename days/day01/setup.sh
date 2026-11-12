#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 01
echo "Preparing Day 01..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: sample-front-a
  labels:
    tier: frontend
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]

---
apiVersion: v1
kind: Pod
metadata:
  name: sample-front-b
  labels:
    tier: frontend
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]

---
apiVersion: v1
kind: Pod
metadata:
  name: sample-back
  labels:
    tier: backend
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 01 ready. Read: $ROOT/days/day01/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
